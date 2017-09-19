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

        name = "Oslo Demo"
        nvdb_id = "826277828"
        unix_epoch = calendar.timegm(time.gmtime())
        # Polygon, Oslo, Grønland
        polygon = [(262906.3971474045, 6649248.441221254),
                   (263059.8558061711, 6649187.586932589),
                   (263022.81406153727, 6649124.086805921),
                   (263816.5657456318, 6648542.002307889),
                   (263943.56601331057, 6648669.00256108),
                   (263803.3365402619, 6650023.6719330065),
                   (262906.3971474045, 6649248.441221254)]

        d.body(name, nvdb_id, unix_epoch, polygon)
        print(d)
        

        self.assertTrue(d.doc.findall("payloadPublication"))
