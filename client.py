#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
import argparse
import logging
import sys
import geofence
import storage
import datex2
import time
from interchange import NordicWayIC

log = logging.getLogger("geofencebroker")
log.setLevel(logging.DEBUG)

ch = logging.StreamHandler(stream=sys.stdout)
log.addHandler(ch)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--broker_url", help="AMQP schemed url to the broker/AMQP server.", required=True)
    parser.add_argument("-v", "--verbose", help="Enable verbose logging / printing", default=False)
    parser.add_argument("-s", "--sender", help="Name of the sender queue", required=True)
    parser.add_argument("-r", "--receiver", help="Name of the receiver queue", required=True)
    parser.add_argument("-k", "--ssl-keyfile", help="SSL key file")
    parser.add_argument("-c", "--ssl-certfile", help="SSL cert file")
    parser.add_argument("-u", "--username", help="Username", default=None)
    parser.add_argument("-p", "--password", help="Password", default=None)

    args = parser.parse_args()

    if args.verbose:
        pass

    options = {"ssl_skip_hostname_check": True}
    if args.ssl_keyfile:
        options.update({"ssl_keyfile": args.ssl_keyfile})
    if args.ssl_certfile:
        options.update({"ssl_certfile": args.ssl_certfile})
    print("options: {}".format(options))

    if args.broker_url.startswith("amqps"):
        # Encrypted amqps session
        if not all([args.ssl_keyfile, args.ssl_certfile]):
            log.error("Broker URL uses TLS/SSL. Therefore you need to specify SSL cert and key.")
            sys.exit(1)

    ic = NordicWayIC(args.broker_url, args.sender, args.receiver,
                     args.username, args.password, options)
    log.debug(ic)
    ic.connect()

    if not ic.connection.opened():
        log.error("Unable to connect!")
        sys.exit(1)

    # Main loop
    while True:
        fences = geofence.fetch_objects()
        if not fences or fences.get("returnert", 0) == 0:
            log.debug("No geofence objects..")

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
                if storage.is_modified(fence):
                    storage.update(geofence)
                    log.info("SCHEDULE A NEW EVENT TO NordicWayIC WITH NEW DATEX2 document!")
                    datex_obj = datex2.create_doc(fence)
                    ic.send_obj(datex_obj)
                else:
                    log.debug("geofence is already in db and has not been updated. Do nothing!")
        else:
            log.debug("Missing 'objekter' in vegobjekter from NVDB: {}".format(fences))

        log.debug(".")
        time.sleep(5)

    ic.close()

    # prop = {
    #     "who": "Norwegian Public Roads Administration",
    #     "how": "Datex2",
    #     "what": "Conditions",
    #     "lat": 63.0,
    #     "lon": 10.01,
    #     "where1": "no",
    #     "when": str(datetime.datetime.now())
    # }
    # m = Message(user_id=args.username, properties=prop, content="Testing testing testing")

    # try:
    #     ic.send_messsage(m)
    # except MessagingError as me:
    #     print("Unable to send message: {}".format(m))
    #     print("Error: {}".format(me))

    # try:
    #     incoming = ic.receiver.fetch(timeout=15.0)
    #     print("Got message: {}".format(incoming))
    # except Empty:
    #     print("Didn't receive any messages...")

    # ic.session.acknowledge()
