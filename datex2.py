# -*- coding: utf-8 -*-

from lxml import etree
import io
import datetime
import pytz


def create_datex_xml(geofence):
    vegobjekter = etree.Element("vegobjekter")
    xml_doc = etree.ElementTree(vegobjekter)

    #####
    vegobjekt1 = etree.SubElement(vegobjekter, "vegobjekt")
    vegobjekt1.attr["id"] = 1
    vegobjekt1.attr["location"] = "Trondheim"


    vegobjekt2 = etree.SubElement(vegobjekter, "vegobjekt")
    vegobjekt2.attr["id"] = 2
    vegobjekt2.attr["location"] = "Åfjord"

    # For debug
    print(etree.tostring(xml_doc, pretty_print=True))
    return xml_doc


class Datex2:
    def __init__(self):
        self._file = io.StringIO()

        self._qname = etree.QName("http://www.w3.org/2001/XMLSchema-instance", "type")

        self.root = etree.Element("payloadPublication", attrib={"lang": "en"})
        self.root.set(self._qname, "PredefinedLocationsPublication")
        self.doc = etree.ElementTree(self.root)

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

    def body(self, name, nvdb_id, unix_epoch, polygon):
        # Add meta information
        self._locationContainer(name, nvdb_id, unix_epoch)

        # Add GPS coordinates to XML document
        self._locationArea(polygon)

    def _locationContainer(self, name, nvdb_id, unix_epoch):
        """
        Adds the <predefinedLocationContainer> XML tag block
        """
        predefinedLocationCont = etree.SubElement(self.root, "predefinedLocationContainer",
                                                  attrib={
                                                      "id": nvdb_id,
                                                      "version": str(unix_epoch)
                                                  })
        predefinedLocationCont.set(self._qname, "PredefinedLocation")
        predefLocContName = etree.SubElement(predefinedLocationCont, "predefinedLocationName")
        locationBlockValues = etree.SubElement(predefLocContName, "values")
        etree.SubElement(locationBlockValues, "value").text = name

    def _locationArea(self, polygon):
        """
        Constructs the polygon XML definitions based on the geofence Polygon
        coordinates from NVDB.
        """
        loc = etree.SubElement(self.root, "location")
        loc.set(self._qname, "Area")

        areaExt = etree.SubElement(loc, "areaExtension")
        openlrExtArea = etree.SubElement(areaExt, "openlrExtendedArea")

        openrlAreaLocRef = etree.SubElement(openlrExtArea, "openlrAreaLocationReference")
        openrlAreaLocRef.set(self._qname, "OpenlrPolygonLocationReference")

        openrlPolygonCorners = etree.SubElement(openrlAreaLocRef, "openlrPolygonCorners")

        for p in polygon:
            # Assume 'p' is a tuple of (lat,lon) coord
            coord = etree.SubElement(openrlPolygonCorners, "openrlCoordinate")
            lat = etree.SubElement(coord, "latitude")
            lat.text = str(p[0])
            lon = etree.SubElement(coord, "longitude")
            lon.text = str(p[1])

    def __str__(self):
        return etree.tostring(self.doc, pretty_print=True)
