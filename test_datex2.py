# -*- coding: utf-8 -*-

from unittest import TestCase
from datex2 import Datex2
import calendar
import time


class TestDatex2(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_document(self):
        d = Datex2()

        self.assertIsNotNone(d)

    def test_add_body(self):
        d = Datex2()

        name = "TestName"
        nvdb_id = "123456"
        unix_epoch = calendar.timegm(time.gmtime())
        polygon = [(69.273653333, 19.944328333), (69.27362, 19.944135)]

        d.body(name, nvdb_id, unix_epoch, polygon)
        print(d)

        self.assertTrue(d.doc.findall("publicationTime"))
        self.assertTrue(d.doc.findall("location"))
