#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
import argparse
import logging
import yaml
import os
import sys
import geofence
import storage
import datex2
import time
from interchange import NordicWayIC

log = logging.getLogger("geofencebroker")
log.setLevel(logging.INFO)

ch = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

log.addHandler(ch)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-conf", "--config", help="Config file that specifies all input parameters", default=None)
    parser.add_argument("-b", "--broker_url", help="AMQP schemed url to the broker/AMQP server.", default=None)
    parser.add_argument("-v", "--verbose", help="Enable verbose logging / printing", default=False)
    parser.add_argument("-s", "--sender", help="Name of the sender queue", default=None)
    parser.add_argument("-r", "--receiver", help="Name of the receiver queue", default=None)
    parser.add_argument("-k", "--ssl-keyfile", help="SSL key file")
    parser.add_argument("-c", "--ssl-certfile", help="SSL cert file")
    parser.add_argument("-u", "--username", help="Username", default=None)
    parser.add_argument("-p", "--password", help="Password", default=None)
    parser.add_argument("-t", "--timeout", type=int,
                        help="Timeout in seconds before checking NVDB for geofence updates", default=300)
    parser.add_argument("-volvotest", help="""Flag to use a test geofence Polygon in sweden
        instead of using the returned data from NVDB. ONLY FOR DEBUGGING.""", default=False)

    args = parser.parse_args()
    cfg = {}

    if args.config:
        log.info("Using config file")
        if not os.path.exists(args.config):
            log.error("Config file was not found..")
            sys.exit(1)
        with open(args.config, 'r') as f:
            cfg = yaml.load(f)

        required_parms = []
        cfg_get = lambda x: cfg.get(x, False)
        map(required_parms.append, [cfg_get("broker_url"), cfg_get("sender"), cfg_get("receiver")])
        if not all(required_parms):
            log.error("Missing required parameters from config file!")
            sys.exit(1)

    else:
        required_parms = []
        map(required_parms.append, [args.broker_url, args.sender, args.receiver])
        log.debug("required_parms: {}".format(required_parms))

        if not all(required_parms):
            log.error("Missing required parameters!")
        sys.exit(1)

    if args.verbose:
        cfg.update({"verbose": True})

    if not cfg.get("timeout"):
        cfg.update({"timeout": args.timeout})

    if cfg.get("verbose", False):
        log.setLevel(logging.DEBUG)

    options = {"ssl_skip_hostname_check": True}
    if cfg.get("ssl_keyfile", False):
        options.update({"ssl_keyfile": cfg.get("ssl_keyfile")})

    if cfg.get("ssl_certfile", False):
        options.update({"ssl_certfile": cfg.get("ssl_certfile")})

    if cfg.get("broker_url", "").startswith("amqps"):
        # Encrypted amqps session
        if not all([cfg.get("ssl_keyfile"), cfg.get("ssl_certfile")]):
            log.error("Broker URL uses TLS/SSL. Therefore you need to specify SSL cert and key.")
            sys.exit(1)

    # if cfg.get("timeout", False):
    #     options.update({})

    ic = NordicWayIC(cfg.get("broker_url"),
                     cfg.get("sender"),
                     cfg.get("receiver"),
                     cfg.get("username"),
                     cfg.get("password"),
                     options)
    log.debug(ic)
    ic.connect()

    if not ic.connection.opened():
        log.error("Unable to connect!")
        sys.exit(1)

    if args.volvotest:
        filename = "volvotest-polygon.txt"
        if not os.path.exists(filename):
            log.error("VOLVOTEST flag set. Can't find input polygon file: '{}'".format(filename))
            sys.exit(1)

        with open(filename, "r") as f:
            volvotest_polygon = f.read()
            print("Volvotest polygon: {}".format(volvotest_polygon))

    sleep_time = cfg.get("timeout")
    log.debug("Sleeping for {} seconds between each check.".format(sleep_time))

    # Main loop
    while True:
        fences = {}
        if not args.volvotest:
            fences = geofence.fetch_objects()

        if args.volvotest:
            log.debug("Using hardcoded test object for volvo testing")
            volvoobj = {
                "metadata": {
                    "type": {
                        "navn": "Volvo-Test-Name"
                    },
                    "sist_modifisert": "2017-09-08 09:33:44"
                },
                "id": 123456789,
                "href": "https://www.vegvesen.no/not-a-valid-url",
                "egenskaper": [
                    {
                        "datatype": 19,
                        "verdi": volvotest_polygon
                    }
                ]
            }
            fences = {
                "objekter": [volvoobj],
                "metadata": {
                    "returnert": 1
                }
            }

        if not fences or fences["metadata"].get("returnert", 0) == 0:
            time.sleep(sleep_time)
            continue

        # TODO: Check if returned JSON has paging. If so, fetch the rest of
        #       the geofence objects
        for fence in fences.get("objekter"):
            log.debug("fence: {}".format(fence))
            if not storage.exists(fence):
                # New object
                log.info("New object - schedule event to NordicWayIC with new datex2 doc")
                datex_obj = datex2.create_doc(fence)
                storage.add(fence)
                ic.send_obj(datex_obj)
            else:

                if args.volvotest:
                    log.debug("Volvotest mode - will continuously send geofence..")
                    datex_obj = datex2.create_doc(fence)
                    ic.send_obj(datex_obj)
                else:
                    if storage.is_modified(fence):
                        storage.update(geofence)
                        log.info("SCHEDULE A NEW EVENT TO NordicWayIC WITH NEW DATEX2 document!")
                        datex_obj = datex2.create_doc(fence)
                        ic.send_obj(datex_obj)
                    else:
                        log.debug("geofence is already in db and has not been updated. Do nothing!")
        #else:
        #    log.debug("Missing 'objekter' in vegobjekter from NVDB: {}".format(fences))

        time.sleep(sleep_time)
    ic.close()

    log.info("Shutdown.. See ya!")
