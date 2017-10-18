#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
import argparse
import logging
import coloredlogs
import yaml
import os
import sys
import geofence
import storage
import datex2
import time
from interchange import NordicWayIC, ConnectionError

log = logging.getLogger("geofencebroker")


def init_logging(debug_env_var):

    field_style_override = coloredlogs.DEFAULT_FIELD_STYLES
    level_style_override = coloredlogs.DEFAULT_LEVEL_STYLES

    logging_level = 'INFO'
    log.setLevel(logging.INFO)

    if os.environ.get(debug_env_var):
        logging_level = 'DEBUG'
        log.setLevel(logging.DEBUG)

    field_style_override['levelname'] = {"color": "magenta", "bold": True}
    level_style_override['debug'] = {"color": "blue"}

    coloredlogs.install(level=logging_level,
                        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
                        level_styles=level_style_override,
                        field_styles=field_style_override)

    # ch = logging.StreamHandler(stream=sys.stdout)
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # ch.setFormatter(formatter)

    # log.addHandler(ch)


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
                        help="Timeout in seconds before checking NVDB for geofence updates", default=None)

    args = parser.parse_args()
    cfg = {}

    init_logging('DEBUG')

    if args.config:
        log.info("Using config file")
        if not os.path.exists(args.config):
            log.error("Config file was not found..")
            sys.exit(1)
        try:
            with open(args.config, 'r') as f:
                cfg = yaml.load(f)
        except yaml.scanner.ScannerError as se:
            log.error("Error parsing config file: {}".format(args.config))
            sys.exit(1)

        required_parms = []
        cfg_get = lambda x: cfg.get(x, False)
        map(required_parms.append, [cfg_get("broker_url"), cfg_get("sender"), cfg_get("receiver")])
        if not all(required_parms):
            log.error("Missing required parameters from config file!")
            sys.exit(1)

    else:
        required_parms = []
        map(required_parms.append,
            [args.broker_url, args.sender, args.receiver])
        log.debug("required_parms: {}".format(required_parms))

        if not all(required_parms):
            log.error("Missing required parameters!")
        sys.exit(1)

    if args.verbose:
        cfg.update({"verbose": True})

    if args.timeout:
        cfg.update({"timeout": args.timeout})

    options = {"ssl_skip_hostname_check": True}
    if cfg.get("ssl_keyfile", False):
        options.update({"ssl_keyfile": cfg.get("ssl_keyfile")})

    if cfg.get("ssl_certfile", False):
        options.update({"ssl_certfile": cfg.get("ssl_certfile")})

    if cfg.get("broker_url", "").startswith("amqps"):
        # Encrypted amqps session
        if not all([cfg.get("ssl_keyfile"), cfg.get("ssl_certfile")]):
            log.error("""Broker URL uses TLS/SSL.
                Therefore you need to specify SSL cert and key.""")
            sys.exit(1)

    log.info("Connecting to {broker_url}".format(**cfg))
    log.info(" sender: {sender}, receiver: {receiver}".format(**cfg))

    ic = NordicWayIC(cfg.get("broker_url"),
                     cfg.get("sender"),
                     cfg.get("receiver"),
                     cfg.get("username"),
                     cfg.get("password"),
                     options)
    log.debug(ic)

    try:
        ic.connect()
    except ConnectionError as e:
        log.error("Unable to connect to {}".format(cfg.get("broker_url")))
        log.error(e)
        sys.exit(1)

    if not ic.connection.opened():
        log.error("Unable to connect!")
        sys.exit(1)

    sleep_time = cfg.get("timeout")
    log.debug("Sleeping for {} seconds between each check.".format(sleep_time))

    # hack to create centroids if missing - a one-time operation!
    storage.fix_centroid()

    # Main loop
    while True:
        fences = geofence.fetch_objects()

        if not fences or fences["metadata"].get("returnert", 0) == 0:
            time.sleep(sleep_time)
            continue

        # TODO: Check if returned JSON has paging. If so, fetch the rest of
        #       the geofence objects
        vegobjekt_ids = []
        try:
            for fence in fences.get("objekter"):
                # Sample all vegobjekt IDs to check if there are anyone that
                # has been deleted from NVDB
                vegobjekt_ids.append(int(fence.get("id", 0)))

                if not storage.exists(fence):
                    log.info("New object - schedule event to NordicWayIC with new datex2 doc")
                    datex_obj = datex2.create_doc(fence)
                    storage.add(fence)
                    ic.send_obj(datex_obj)
                else:
                    if storage.is_modified(fence):
                        storage.update(fence)
                        datex_obj = datex2.create_doc(fence)
                        log.info("New event: message: version={}, name={}"
                                 .format(datex_obj.version, datex_obj.name))
                        ic.send_obj(datex_obj)
                    else:
                        log.debug("geofence is already in db and has not been updated.")


            # Find deleted vegobjekter in NVDB by getting a list of ID's from our 
            # cache database and list all ID's missing in our JSON from NVDB.
            vegobjekter = storage.vegobjekter().all()
            for v in vegobjekter:
                log.info("inspecting v: {}".format(v.get("id")))
                if v.get("id") not in vegobjekt_ids:
                    log.warn("Vegobjekt with ID '{}' removed from NVDB: {}".format(v.get("id"), v))
                    datex_obj = datex2.create_delete_doc_from_db(v)
                    ic.send_obj(datex_obj)
                    log.debug(datex_obj)
                    storage.delete(v.get("id"))
                    log.warn("Delete geofence id: {}".format(v.get("id")))


        except ConnectionError:
            # Interchange lost its connection
            log.debug("Interchange connection error. Trying to re-connect. URI: {}".format(cfg.get("broker_url")))
            while True:
                try:
                    ic.connect()
                    log.debug("Successfully re-connected to {}".format(cfg.get("broker_url")))
                except ConnectionError:
                    log.debug("")
                    time.sleep(5)
                    continue
                break

        time.sleep(sleep_time)
    ic.close()

    log.info("Shutdown.. See ya!")
