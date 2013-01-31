import re
import urllib
import logging
import urllib2
import urlparse
import contextlib

from lxml import etree

from .utils import clear_xml_namespaces, clear_xml_comments

logger = logging.getLogger('wpsutils.wps')

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
        return clear_xml_comments(clear_xml_namespaces(etree.XML(data, parser)))

class WpsAbstractConnection(XMLConnection):
    def __init__(self, url):
        super(WpsAbstractConnection, self).__init__(url)

    def process_wps_errors(self, document):
        exception_root = document.getroot()
        print etree.tostring(exception_root)
        try:
            code = exception_root.find("Exception").get("exceptionCode")
        except AttributeError:
            return document 
        else:
            #TODO: find a better way to do this ...
            try:
                text = exception_root.find("Exception").find("ExceptionText").text
            except AttributeError:
                text = ""
            raise WpsError(code, text)

class WpsConnection(WpsAbstractConnection):
    def __init__(self, wps_request_url):
        super(WpsConnection, self).__init__(wps_request_url)

    def do_request(self, request, data=None):
        data = data if data is not None else {}
        data.update({'Service':'WPS', 'Request':request, 'Version':'1.0.0'})
        clean_document = self.process_wps_errors(self.do_xml_request('GET', data)) 
        return clean_document 

    def get_process_list(self):
        document = self.do_request('GetCapabilities') 
        return [{'identifier':process.find("Identifier").get('text', ""),
                 'version':process.get("processVersion"),
                 'title':process.find("Title").get('text', "")}
                for process in document.find("ProcessOfferings")] 

    def get_process_details(self, process_name):
        document = self.do_request('DescribeProcess', {'Identifier':process_name})
        root = document.find("ProcessDescription")
        inputs_tree = root.find("DataInputs")
        outputs_tree = root.find("ProcessOutputs")

        inputs = [{'identifier':input.find("Identifier").get('text', ""),
                   'type':input.find("LiteralData").find("DataType").get("reference"),
                   'title':input.find("Title").get('text', ""),
                   'abstract':input.find("Abstract").get('text', ""),}
                  for input in inputs_tree.findall("Input")]

        outputs = [{'identifier': output.find("Identifier").get('text', ""),
                    'title': output.find("Title").get('text', ""),
                    'abstract': output.find("Abstract").get('text', ""),}
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

class WpsResultConnection(WpsAbstractConnection):
    def __init__(self, wps_polling_url):
        parsed_url = urlparse.urlparse(wps_polling_url)
        polling_url = "%s://%s%s" % parsed_url[:3] 
        super(WpsResultConnection, self).__init__(polling_url) 
        self.inputs = [tuple(input_data.split("=")) for input_data in parsed_url[4].split(',')]

    def do_request(self):
        return self.process_wps_errors(
                self.do_xml_request('GET', self.inputs))

    def _parse_outputs(self, output_tag):
        transform = lambda s: '_'.join([w.lower() for w in re.findall("[A-Z][a-z]+", s)])

        outputs = [{'identifier':output.find("Identifier").text,
                    'title':output.find("Title").text,
                    transform(output.find("Data")[0].tag):output.find("Data")[0].text
                    } for output in output_tag]
        return outputs

    def _has_exception(self, output_list):
        for out in output_list:
            if out['identifier'] == 'EXCEPTION' and \
                (out['literal_data'] is not None and out['literal_data'] != ""):
                return out
        return False


    def get_polling_status(self):
        """
        This function will query the process polling page and return
        a two element tuple containing (<status>, <payload>).
        The payload will be a dictionary object or None.
        As OGC 05-007r7 document states at page 59,
        table 55 the possible statuses of a process are:
        - ProcessAccepted:
          * Process has been accepted and queued by the server but processing has not begun.
          * status = 'accepted'
          * payload = verbose message by the wps [or None].
        - ProcessStarted:
          * Process has been accepted by the server and processing has begun.
          * status = 'started'
          * payload = verbose message and possibly a percentCompleted value [or None].
        - ProcessPaused:
          * The server has paused the process.
          * status = 'paused'
          * payload = verbose message and possibly a percentCompleted value [or None].
        - ProcessSucceeded:
          * The process has successfully completed its execution.
          * status = 'succeeded'
          * payload = verbose message and outputs of the project
        - ProcessFailed: execution of the process has failed.
          * Execution of the process has failed.
          * status = 'failed'
          * payload = TODO: to be defined 
        Most of this is not yet implemented.
        """

        logger.debug( 'polling at url: %s, inputs are %s' % \
                (self.url, self.inputs))

        document = self.do_request()
        status_tag = document.find("Status")
        status = status_tag[0].tag

        retval = None

        if status == "ProcessAccepted":
            retval = ('accepted', None)
        elif status == "ProcessStarted":
            retval = ('started', None)
        elif status == "ProcessPaused":
            retval = ('paused', None)
        elif status == "ProcessSucceeded":
            outputs = self._parse_outputs(
                    document.find("ProcessOutputs"))
            exception = self._has_exception(outputs)

            if exception:
                retval = ('failed', exception)
            else:
                retval = ('succeeded', outputs)

        elif status == "ProcessFailed":
            retval = ('failed', None)
        
        assert retval is not None

        return retval
