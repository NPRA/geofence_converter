# -*- coding: utf-8 -*-

import dataset
import logging
from util import parse_timestamp

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

db = dataset.connect("sqlite:///database.db")


def vegobjekter():
    table_vegobjekter = db.get_table("vegobjekter")
    return table_vegobjekter


def exists(vegobjekt):
    table_vegobjekter = db.get_table("vegobjekter")
    if table_vegobjekter.find_one(id=vegobjekt.get("id")):
        return True
    return False


def add(vegobjekt):
    # import pdb; pdb.set_trace()
    table_vegobjekter = db.get_table("vegobjekter")

    geofence = convert_to_geofence(vegobjekt)
    table_vegobjekter.insert(geofence)


def convert_to_geofence(vegobjekt):
    """
    'datatype' == 19 -> GeomFlate, ref NVDB api explanation for vegobjekter
    """
    tmp = [x for x in vegobjekt.get("egenskaper") if x["datatype"] == 19]
    if not tmp:
        log.error("Unable to find GeomFlate from vebobjekt. Something is wrong! {}".format(tmp))
        return None
    geomFlate = tmp[0]

    if "POLYGON" not in geomFlate.get("verdi"):
        log.error("Missing POLYGON in 'verdi' key! {}".format(geomFlate))
        return None

    # Convert all polygon coordinates to a proper list of UTM coordinates
    # polygon_coords = geomFlate.get("verdi").replace("POLYGON ((", "")
    # polygon_coords = polygon_coords.replace("))", "")
    # polygon_coords = polygon_coords.split(",")
    # coords = [x.strip().split(" ") for x in polygon_coords]
    # for i, c in enumerate(coords):
    #     coords[i][0] = float(c[0])
    #     coords[i][1] = float(c[1])

    geofence = {
        "id": vegobjekt["id"],
        "href": vegobjekt["href"],
        "sist_modifisert": vegobjekt["metadata"]["sist_modifisert"],
        "type": vegobjekt["metadata"]["type"]["navn"],
        "polygon": geomFlate.get("verdi")
    }

    return geofence


def is_modified(vegobjekt):
    # import pdb; pdb.set_trace()
    next_date = parse_timestamp(vegobjekt["metadata"]["sist_modifisert"])

    table_vegobjekter = db.get_table("vegobjekter")
    geofence = table_vegobjekter.find_one(id=vegobjekt.get("id"))
    if not geofence:
        log.warn("vegobjekt not found in database")
        return False

    prev_date = parse_timestamp(geofence["sist_modifisert"])

    if next_date > prev_date:
        # 'vegobjekt' har blitt modifisert
        return True
    elif next_date < prev_date:
        log.warn("next_date < prev_data: (%s < %s)" % (next_date, prev_date))
        log.warn("Most likely a bug!!")
    return False


def update(vegobjekt):
    table_vegobjekter = db.get_table("vegobjekter")

    geofence = convert_to_geofence(vegobjekt)
    table_vegobjekter.update(vegobjekt, ['id'])
