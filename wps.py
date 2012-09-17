import urllib
import urllib2
import contextlib

from lxml import etree

from utils import url_join, clear_xml_namespaces

class XMLConnection(object):
    def __init__(self, host, path):
        self._host = host
        self._path = path
    
    @property
    def url(self):
        return url_join(self._host, self._path)

    def _doRequest(self, req_type, data, headers=None):
        """
        Executes a request to the wps and returns the response object.
        """
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

    def doXMLRequest(self, req_type, data):
        with contextlib.closing(self._doRequest(req_type, data)) as response:
            data = response.read()

        parser = etree.XMLParser(remove_blank_text=True)
        return clear_xml_namespaces(etree.XML(data, parser))

class WpsConnection(XMLConnection):
    def __init__(self, wps_address, wps_request_path):
        XMLConnection.__init__(self, wps_address, wps_request_path)

    def doRequest(self, request, data=None):
        data = data if data is not None else {}
        data.update({'Service':'WPS', 'Request':request})
        return self.doXMLRequest('GET', data)

    def getProcessList(self):
        document = self.doRequest('GetCapabilities') 
        return [{'identifier':process.find("Identifier").text,
                 'version':process.get("processVersion"),
                 'title':process.find("Title").text}
                for process in document.find("ProcessOfferings")] 

    def getProcessDetails(self, process_name):
        document = self.doRequest('DescribeProcess', {'Identifier':process_name})

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
        document = self.doRequest('Execute', {'Identifier':process_name,
                                              'Version':"1.0.0",
                                              'DataInputs':processed_inputs,
                                              'ResponseDocument':processed_outputs,
                                              'StoreExecuteResponse':"True",
                                              'Status':"True"})

        return document.getroot().get("statusLocation")
