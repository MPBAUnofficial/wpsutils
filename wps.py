#!/usr/bin/pyhthon

from __future__ import print_function

import io
import urllib
import urllib2
from lxml import etree

from utils import url_join

# xml stuff
wpsNamespace = 'http://www.opengis.net/wps/1.0.0'
owsNamespace = 'http://www.opengis.net/ows/1.1'

xslt="""<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml" indent="no"/>

<xsl:template match="/|comment()|processing-instruction()">
    <xsl:copy>
      <xsl:apply-templates/>
    </xsl:copy>
</xsl:template>

<xsl:template match="*">
    <xsl:element name="{local-name()}">
      <xsl:apply-templates select="@*|node()"/>
    </xsl:element>
</xsl:template>

<xsl:template match="@*">
    <xsl:attribute name="{local-name()}">
      <xsl:value-of select="."/>
    </xsl:attribute>
</xsl:template>
</xsl:stylesheet>
"""

class WpsServer(object):
    """
    Commodity class to connect to a wps server and make requests to it.
    """
    def __init__(self, wps_address, wps_path):
        self._wps_address = wps_address
        self._wps_path = wps_path
        self._required_args = {'Service':'WPS'}
        

    @property
    def url(self):
        return url_join(self._wps_address, self._wps_path)

    def _doRequest(self, req_type, data, headers=None):
        data.update(self._required_args)
        if headers is None:
            headers = {}
        
        if req_type == 'GET':
            return self._doGet(data, headers)
        elif req_type == 'POST':
            return self._doPost(data, headers)
        else:
            raise Exception("request type {req_type} not supported".format(req_type=req_type))

    def _doGet(self, data, headers):
        encoded_data = urllib.urlencode(data)
        complete_url = self.url + '?' + encoded_data
        request = urllib2.Request(url=complete_url, headers=headers)
        return urllib2.urlopen(request)

    def _doPost(self, data, headers):
        encoded_data = urllib.urlencode(data)
        request = urllib2.Request(self.url, encoded_data, headers=headers)
        return urllib2.urlopen(request)

    def doXMLRequest(self, req_type, request, **kwargs):
        """
        Executes a HTTP request parsing the response as XML.
        Returns a etree.XML object.
        """
        parser = etree.XMLParser(remove_blank_text=True)
        xslt_doc = etree.parse(io.BytesIO(xslt))
        transform = etree.XSLT(xslt_doc)
        kwargs.update({'Request':request})
        response = self._doRequest(req_type, kwargs)
        return transform(etree.XML(response.read(), parser))

    def getProcessList(self):
        document = self.doXMLRequest('GET', 'GetCapabilities')
        return [{'identifier':process.find("Identifier").text,
                 'version':process.get("processVersion"),
                 'title':process.find("Title").text }
                for process in document.find("ProcessOfferings")] 


    def getProcessDetails(self, process_name):
        document = self.doXMLRequest('GET', 'DescribeProcess',
                Identifier=process_name)

        root = document.find("ProcessDescription")
        inputs_tree = root.find("DataInputs")
        outputs_tree = root.find("ProcessOutputs")

        inputs = [{'identifier':input.find("Identifier").text,
                   'type':input.find("LiteralData").find("DataType").get("reference")}
                  for input in inputs_tree.findall("Input")]

        outputs = [{'identifier': output.find("Identifier").text,} 
                   for output in outputs_tree.findall("Output")]

        return {'inputs':inputs, 'outputs':outputs} 
