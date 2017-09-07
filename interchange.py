# -*- coding: utf-8 -*-

import sys
import logging

log = logging.getLogger("geofence.interchange")
log.setLevel(logging.DEBUG)

try:
    from qpid.messaging import Connection, Message, MessagingError, Empty
except ImportError as ie:
    log.exception("Unable to find 'qpid' module. Do you have it in sys.path / PYTHONPATH?")
    sys.exit(1)


class NordicWayIC:
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
        try:
            self.sender.send(msg)
            self.sender.check_error()
        except MessagingError:
            log.exception("Error sending message!")

    def close(self):
        self.connection.close()

    def __repr__(self):
        return "<{} url={}, sender={}, receiver={}, options={}>".format(
            self.__class__.__name__, self.url,
            self._queue_sender, self._queue_receiver, self.options)
