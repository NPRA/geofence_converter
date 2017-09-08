# -*- coding: utf-8 -*-

import sys
import logging
import util


try:
    from qpid.messaging import Connection, Message, MessagingError, Empty
except ImportError as ie:
    logging.exception("Unable to find 'qpid' module. Do you have it in sys.path / PYTHONPATH?")
    sys.exit(1)


class NordicWayIC:
    def __init__(self, url, sender, receiver, username, password, options=None):
        self.options = options if options else {}
        self.url = url
        self._queue_sender = sender
        self._queue_receiver = receiver
        self._credentials = {"username": username, "password": password}
        self.log = logging.getLogger("geofencebroker")

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

    def send_obj(self, datex_obj):
        """
        prop = {
    #     "who": "Norwegian Public Roads Administration",
    #     "how": "Datex2",
    #     "what": "Conditions",
    #     "lat": 63.0,
    #     "lon": 10.01,
    #     "where1": "no",
    #     "when": str(datetime.datetime.now())
    # }
    # m = Message(user_id=args.username, properties=prop, content="Testing testing testing")
        """

        centroid = util.utm_to_gps(datex_obj.centroid)


        prop = {
            "who": "Norwegian Public Roads Administration",
            "how": "Datex2",
            "what": "Conditions",
            "lat": centroid[0],
            "lon": centroid[1],
            "where1": "no",
            "when": str(datetime.datetime.now())
        }

        m = Message(user_id=self._credentials.get("username"),
                    properties=prop,
                    content=str(datex_obj))

        print("Sending message: {}".format(m))
        print("Datex2 XML: {}".format(str(datex_obj)))

        self.send_messsage(m)

    def close(self):
        self.connection.close()

    def __repr__(self):
        return "<{} url={}, sender={}, receiver={}, options={}>".format(
            self.__class__.__name__, self.url,
            self._queue_sender, self._queue_receiver, self.options)
