# -*- coding: utf-8 -*-

import dataset
import logging
from util import parse_timestamp, parse_polygon, get_polygon_centroid, utm_to_gps
import geofence

# Initialize and connect to local sqlite database
db = dataset.connect("sqlite:///database.db")


def vegobjekter():
    table_vegobjekter = db.get_table("vegobjekter")
    return table_vegobjekter


def exists(vegobjekt):
    table_vegobjekter = db.get_table("vegobjekter")
    if table_vegobjekter.find_one(id=vegobjekt.get("id")):
        return True
    return False


def delete(geofence_id):
    table = vegobjekter()
    table.delete(id=geofence_id)


def add(vegobjekt):
    table_vegobjekter = db.get_table("vegobjekter")
    geofence = convert_to_geofence(vegobjekt)

    nvdb_polygon = geofence.get("polygon")
    polygon = parse_polygon(nvdb_polygon)
    centroid = get_polygon_centroid(polygon)

    geofence["centroid"] = ','.join(map(str, [centroid[0], centroid[1]]))

    table_vegobjekter.insert(geofence)


def convert_to_geofence(vegobjekt):
    """
    'datatype' == 19 -> GeomFlate, ref NVDB api explanation for vegobjekter
    """
    log = logging.getLogger("geofencebroker")

    tmp = [x for x in vegobjekt.get("egenskaper") if x["datatype"] == 19]
    if not tmp:
        log.error("Unable to find GeomFlate from vebobjekt. Something is wrong! {}".format(tmp))
        return None
    geomFlate = tmp[0]

    if "POLYGON" not in geomFlate.get("verdi"):
        log.error("Missing POLYGON in 'verdi' key! {}".format(geomFlate))
        return None

    geofence_obj = {
        "id": vegobjekt["id"],
        "name": geofence.get_name(vegobjekt),
        "href": vegobjekt["href"],
        "sist_modifisert": vegobjekt["metadata"]["sist_modifisert"],
        "version": geofence.get_version(vegobjekt),
        "type": vegobjekt["metadata"]["type"]["navn"],
        "polygon": geomFlate.get("verdi")
    }

    return geofence_obj


def is_modified(vegobjekt):
    # import pdb; pdb.set_trace()
    log = logging.getLogger("geofencebroker")
    next_date = parse_timestamp(vegobjekt["metadata"]["sist_modifisert"])

    table_vegobjekter = db.get_table("vegobjekter")
    geofence = table_vegobjekter.find_one(id=vegobjekt.get("id"))
    if not geofence:
        log.warn("vegobjekt not found in database")
        return False

    prev_date = parse_timestamp(geofence["sist_modifisert"])

    if next_date > prev_date:
        # 'vegobjekt' has been modified
        return True
    elif next_date < prev_date:
        log.warn("next_date < prev_data: (%s < %s)" % (next_date, prev_date))
        log.warn("Most likely a bug!!")
    return False


def fix_centroid():
    """Fixes missing centroids if anyone, since we didn't store that before
    """
    log = logging.getLogger("geofencebroker")
    table_vegobjekter = vegobjekter()

    rows = list(table_vegobjekter.find(centroid=None))
    for row in rows:
        nvdb_polygon = row.get("polygon")
        polygon = parse_polygon(nvdb_polygon)
        centroid = get_polygon_centroid(polygon)

        row["centroid"] = ','.join(map(str, [centroid[0], centroid[1]]))

        update_data = {
            'id': row.get("id"),
            'centroid': row["centroid"]
        }

        table_vegobjekter.update(update_data, ['id'])
        log.info("Updated geofence object {} with centroid".format(row.get("id")))

    return True


def update(vegobjekt):
    table_vegobjekter = db.get_table("vegobjekter")
    geofence = convert_to_geofence(vegobjekt)

    nvdb_polygon = geofence.get("polygon")
    polygon = parse_polygon(nvdb_polygon)
    centroid = get_polygon_centroid(polygon)

    geofence["centroid"] = ','.join(map(str, [centroid[0], centroid[1]]))

    table_vegobjekter.update(geofence, ['id'])
