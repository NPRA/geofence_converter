# -*- coding: utf-8 -*-

import datetime

def parse_timestamp(timestamp):
    return datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")