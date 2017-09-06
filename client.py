#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
import argparse
import logging
import sys
import datetime
import geofence

try:
    from qpid.messaging import Connection, Message, MessagingError, Empty
except ImportError:
    print("Unable to find 'qpid' module. Do you have it in sys.path / PYTHONPATH?")
    sys.exit(1)

log = logging.getLogger("geofencebroker")
log.setLevel(logging.DEBUG)

ch = logging.StreamHandler(stream=sys.stdout)
log.addHandler(ch)



class NordicWaysIC:
    def __init__(self, url, sender, receiver, username, password, options=None):
        self.options = options if options else {}
        self.url = url
        self._queue_sender = sender
        self._queue_receiver = receiver
        self._credentials = {"username": username, "password": password}

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def connect(self):
        self.connection = Connection(self.url,
                                     username=self._credentials.get("username"),
                                     password=self._credentials.get("password"),
                                     **self.options)

        self.connection.open()
        self.session = self.connection.session()

        self.sender = self.session.sender(self._queue_sender)
        self.receiver = self.session.receiver(self._queue_receiver)

    def send_messsage(self, msg):
        self.sender.send(msg)
        self.sender.check_error()
        print("Sent msg: {}".format(msg))

    def close(self):
        self.connection.close()

    def __repr__(self):
        return "<{} url={}, sender={}, receiver={}, options={}>".format(
            self.__class__.__name__, self.url,
            self._queue_sender, self._queue_receiver, self.options)


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

    ic = NordicWaysIC(args.broker_url, args.sender, args.receiver,
                      args.username, args.password, options)
    log.debug(ic)

    ic.connect()
    if not ic.connection.opened():
        log.error("Unable to connect!")
        sys.exit(1)

    # Main loop
    while True:
        fences = geofence.fetch_objects()
        if fences:
            pass

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
