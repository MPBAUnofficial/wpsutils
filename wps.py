import urllib
import urllib2
import contextlib

from lxml import etree

from utils import clear_xml_namespaces

class WpsError(RuntimeError):
    def __init__(self, code, text):
        RuntimeError.__init__(self, text)
        self.code = code
        self.text = text

class XMLConnection(object):
    def __init__(self, url):
        self.url = url

    def _do_request(self, req_type, data, headers=None):
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

    def do_xml_request(self, req_type, data):
        with contextlib.closing(self._do_request(req_type, data)) as response:
            data = response.read()

        parser = etree.XMLParser(remove_blank_text=True)
        return clear_xml_namespaces(etree.XML(data, parser))

class WpsConnection(XMLConnection):
    def __init__(self, wps_request_url):
        XMLConnection.__init__(self, wps_request_url)

    def process_wps_errors(self, document):
        exception_root = document.getroot()
        try:
            code = exception_root.find("Exception").get("exceptionCode")
            text = exception_root.find("Exception").find("ExceptionText").text
        except AttributeError:
            return document 
        else:
            raise WpsError(code, text)

    def do_request(self, request, data=None):
        data = data if data is not None else {}
        data.update({'Service':'WPS', 'Request':request})
        clean_document = self.process_wps_errors(self.do_xml_request('GET', data))
        return clean_document 

    def get_process_list(self):

        document = self.do_request('GetCapabilities') 
        return [{'identifier':process.find("Identifier").text,
                 'version':process.get("processVersion"),
                 'title':process.find("Title").text}
                for process in document.find("ProcessOfferings")] 

    def get_process_details(self, process_name):
        document = self.do_request('DescribeProcess', {'Identifier':process_name})

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

    def run_process(self, process_name, data_inputs):
        # Soluzione elegante
        #processed_data = ';'.join(["{0}={1}".format(*item) for item in data_inputs.items()])
        # Soluzione meno elegante
        processed_outputs = ';'.join([out['identifier'] for out in self.get_process_details(process_name)['outputs']])
        processed_inputs = ';'.join(["%s=%s"%item for item in data_inputs.items()])
        document = self.do_request('Execute', {'Identifier':process_name,
                                              'Version':"1.0.0",
                                              'DataInputs':processed_inputs,
                                              'ResponseDocument':processed_outputs,
                                              'StoreExecuteResponse':"True",
                                              'Status':"True"})

        return document.getroot().get("statusLocation")
