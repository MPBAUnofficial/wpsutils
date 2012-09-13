import urllib
import urllib2
import contextlib

from lxml import etree

from utils import url_join, clear_xml_namespaces

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
        """
        Executes a request to the wps and returns the response object.
        """
        data.update(self._required_args)
        headers = headers if headers is not None else {}
        encoded_data = urllib.urlencode(data)

        if req_type == 'GET':
            request = urllib2.Request(self.url + "?" + encoded_data,
                    headers=headers) 
        elif req_type == 'POST':
            request = urllib2.Request(self.url, encoded_data,
                    headers=headers)
        else:
            raise Exception("request type {req_type} not supported".format(req_type=req_type))

        return urllib2.urlopen(request)

    def doXMLRequest(self, req_type, request, **kwargs):
        """
        Executes a HTTP request parsing the response as XML.
        If namespaces are used they will be removed.
        Returns a etree.XML object if everything goes well,
        it propagates the exception otherwise.
        """
        kwargs.update({'Request':request})

        with contextlib.closing(self._doRequest(req_type, kwargs)) as response:
            data = response.read()

        parser = etree.XMLParser(remove_blank_text=True)
        return clear_xml_namespaces(etree.XML(data, parser))

    def getProcessList(self):
        document = self.doXMLRequest('GET', 'GetCapabilities')
        return [{'identifier':process.find("Identifier").text,
                 'version':process.get("processVersion"),
                 'title':process.find("Title").text}
                for process in document.find("ProcessOfferings")] 

    def getProcessDetails(self, process_name):
        document = self.doXMLRequest('GET', 'DescribeProcess',
                Identifier=process_name)

        root = document.find("ProcessDescription")
        inputs_tree = root.find("DataInputs")
        outputs_tree = root.find("ProcessOutputs")

        inputs = [{'identifier':input.find("Identifier").text,
                   'type':input.find("LiteralData").find("DataType").get("reference"),
                   'title':input.find("Title").text,
                   'abstract':input.find("Abstract").text,}
                  for input in inputs_tree.findall("Input")]

        outputs = [{'identifier': output.find("Identifier").text, 
                    'title': output.find("Title").text,
                    'abstract': output.find("Abstract").text,}
                   for output in outputs_tree.findall("Output")]

        return {'inputs':inputs, 'outputs':outputs} 

    def runProcess(self, process_name, data_inputs):
        # Soluzione elegante
        #processed_data = ';'.join(["{0}={1}".format(*item) for item in data_inputs.items()])
        # Soluzione meno elegante
        processed_outputs = ';'.join([out['identifier'] for out in self.getProcessDetails(process_name)['outputs']])
        processed_inputs = ';'.join(["%s=%s"%item for item in data_inputs.items()])
        document = self.doXMLRequest('GET', 'Execute',
                                        Identifier=process_name,
                                        Version="1.0.0",
                                        DataInputs=processed_inputs,
                                        ResponseDocument=processed_outputs,
                                        StoreExecuteResponse="True",
                                        Status="True")

        return document.getroot().get("statusLocation")
