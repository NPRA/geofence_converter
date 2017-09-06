# -*- coding: utf-8 -*-

import requests
from requests.exceptions import ConnectionError
import logging

log = logging.getLogger(__name__)


def fetch_objects():
    try:
        url = "https://www.utv.vegvesen.no/nvdb/api/v2/vegobjekter/911?segmentering=true&inkluder=lokasjon,egenskaper,metadata&kartutsnitt=-621912,6250000,1821912,8189887"
        req = requests.get(url)

        if not req.ok:
            log.warn("Unable to retrieve NVDB goefence objects")
            return None
        return req.json()
    except ConnectionError as ce:
        log.exception(ce)
        return None
