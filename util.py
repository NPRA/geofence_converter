# -*- coding: utf-8 -*-

import datetime
import calendar
import utm
import six


def datetime_to_unix_epoch(timestamp):
    """Converts datetime instance to UNIX epoch time
    """
    return calendar.timegm(timestamp.timetuple())


def parse_timestamp(timestamp):
    """New datetime object parse from a string (timestamp)
    """
    return datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")


def utm_to_gps(utm_coordinate, zone=33, zone_letter='N'):
    """
    Converts UTM coordinate to GPS lat, lon.

    Defaults to zone number 33 (Norway) and letter 'N'.
    """
    return utm.to_latlon(utm_coordinate[0], utm_coordinate[1], zone, zone_letter)


def parse_polygon(nvdb_polygon):
    """Converts NVDB polygon (string) into a 2D python list of float UTM coords:
    From: POLYGON ((261406.25545925 6649329.53490491, 261418.543820197 6649292.41831282))
    To: [(261406.25545925, 6649329.53490491), (261418.543820197, 6649292.41831282)]
    """

    if not isinstance(nvdb_polygon, six.string_types):
        raise ValueError("Invalid input argument: expected string, got {}".format(type(nvdb_polygon)))

    tmp = nvdb_polygon.replace("POLYGON ((", "").replace("))", "")
    polygon = [x.strip().split(" ") for x in tmp.split(",")]
    return polygon


def get_polygon_centroid(polygon_input):
    """Calculates centroid from the 2D input list of UTM coordinates.
    ref https://stackoverflow.com/questions/2792443/finding-the-centroid-of-a-polygon
    """

    polygon = polygon_input
    if isinstance(polygon_input[0][0], six.string_types):
        polygon = [[float(i) for i in p] for p in polygon_input]

    centroid = [0.0, 0.0]
    signed_area = 0.0
    a = 0.0
    p_length = len(polygon) - 1

    for i in range(p_length):
        x0, y0 = polygon[i][0], polygon[i][1]
        x1, y1 = polygon[i + 1][0], polygon[i + 1][1]

        a = x0 * y1 - x1 * y0
        signed_area += a
        centroid[0] += (x0 + x1) * a
        centroid[1] += (y0 + y1) * a

    x0, y0 = polygon[p_length][0], polygon[p_length][1]
    x1, y1 = polygon[0][0], polygon[0][1]
    a = x0 * y1 - x1 * y0
    signed_area += a
    centroid[0] += (x0 + x1) * a
    centroid[1] += (y0 + y1) * a

    signed_area *= 0.5

    try:
        centroid[0] /= (6.0 * signed_area)
        centroid[1] /= (6.0 * signed_area)
    except ZeroDivisionError:
        raise
    else:
        return tuple(centroid)
