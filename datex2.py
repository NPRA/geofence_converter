# -*- coding: utf-8 -*-

from lxml import etree
import io
import datetime
import pytz
import logging
import geofence
import util

log = logging.getLogger("geofencebroker")


def create_doc(vegobjekt):
    doc = Datex2()

    name = geofence.get_name(vegobjekt)
    nvdb_id = vegobjekt["id"]
    version = geofence.get_version(vegobjekt)
    polygon = geofence.get_polygon(vegobjekt)

    polygon = [[float(j) for j in i] for i in polygon]
    centroid = util.get_polygon_centroid(polygon)

    doc.body(name, nvdb_id, version, polygon, centroid)

    log.debug("Creating new Datex2 document: name={}, nvdb_id={}, version={}".format(
        name, nvdb_id, version))
    return doc


class Datex2:
    def __init__(self):
        self._file = io.StringIO()

        self.top_root = etree.Element("d2LogicalModel",
                                      attrib={"modelBaseVersion": "2"},
                                      nsmap={None: "http://datex2.eu/schema/2/2_0"})
        self.doc = etree.ElementTree(self.top_root)

        exchange = etree.SubElement(self.top_root, "exchange")
        supplierId = etree.SubElement(exchange, "supplierIdentification")
        etree.SubElement(supplierId, "country").text = "no"
        etree.SubElement(supplierId, "nationalIdentifier").text = "Norwegian Public Roads Administration"

        self.root = etree.SubElement(self.top_root, "payloadPublication", attrib={"lang": "en"})
        self._qname = etree.QName("http://www.w3.org/2001/XMLSchema-instance", "type")
        self.root.set(self._qname, "PredefinedLocationsPublication")

        self._header()

    def _header(self):
        """
        Construct the standard Datex2 header
        """
        pubTime = etree.SubElement(self.root, "publicationTime")
        tz = pytz.timezone("Europe/Oslo")
        pubTime.text = datetime.datetime.now(tz).isoformat()

        pubCreator = etree.SubElement(self.root, "publicationCreator")
        etree.SubElement(pubCreator, "country").text = "no"
        etree.SubElement(pubCreator, "nationalIdentifier").text = "Norwegian Public Roads Administration"

        headerInformation = etree.SubElement(self.root, "headerInformation")
        etree.SubElement(headerInformation, "confidentiality").text = "noRestriction"
        etree.SubElement(headerInformation, "informationStatus").text = "real"

    def body(self, name, nvdb_id, version, polygon, centroid):
        # Temporary storing of polygon
        gps_coords_poly = [util.utm_to_gps(i) for i in polygon]

        # Add meta information
        self._locationContainer(name, nvdb_id, version, gps_coords_poly)

        self.polygon = gps_coords_poly

        log.debug("polygon: {}".format(polygon))
        log.debug("gps coords: {}".format(gps_coords_poly))

        # Calculate centroid of the polygon
        # self.centroid = geofence.get_polygon_centroid(polygon)
        self.centroid = centroid
        log.debug("Datex2 centroid: {}".format(self.centroid))
        self.centroid = util.utm_to_gps(self.centroid)

        self.name = name
        self.nvdb_id = nvdb_id
        self.version = version

    def _locationContainer(self, name, nvdb_id, version, polygon):
        """
        Adds the <predefinedLocationContainer> XML tag block
        """
        predefinedLocationCont = etree.SubElement(self.root, "predefinedLocationContainer",
                                                  attrib={
                                                      "id": unicode(nvdb_id),
                                                      "version": unicode(version)
                                                  })
        predefinedLocationCont.set(self._qname, "PredefinedLocation")
        predefLocContName = etree.SubElement(predefinedLocationCont, "predefinedLocationName")
        locationBlockValues = etree.SubElement(predefLocContName, "values")
        etree.SubElement(locationBlockValues, "value").text = name

        self._locationArea(predefinedLocationCont, polygon)

    def _locationArea(self, parent, polygon):
        """
        Constructs the polygon XML definitions based on the geofence Polygon
        coordinates from NVDB.
        """
        loc = etree.SubElement(parent, "location")
        loc.set(self._qname, "Area")

        areaExt = etree.SubElement(loc, "areaExtension")
        openlrExtArea = etree.SubElement(areaExt, "openlrExtendedArea")

        openrlAreaLocRef = etree.SubElement(openlrExtArea, "openlrAreaLocationReference")
        openrlAreaLocRef.set(self._qname, "OpenlrPolygonLocationReference")

        openrlPolygonCorners = etree.SubElement(openrlAreaLocRef, "openlrPolygonCorners")

        for p in polygon:
            # Assume 'p' is a tuple of (lat,lon) coord
            coord = etree.SubElement(openrlPolygonCorners, "openlrCoordinate")
            lat = etree.SubElement(coord, "latitude")
            lat.text = str(p[0])
            lon = etree.SubElement(coord, "longitude")
            lon.text = str(p[1])

    def __str__(self):
        return etree.tostring(self.doc, pretty_print=True)
