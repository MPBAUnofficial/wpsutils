from django.http import HttpResponseBadRequest

from tojson import render_to_json
from .models import WpsServer
from .wps import WpsError

class DispatchError(RuntimeError):
    def __init__(self, payload):
        RuntimeError.__init__(self)
        self.payload = payload

def dispatch_errors(function):
    def _inner(request, **kwargs):
        try:
            return function(request, **kwargs)
        except DispatchError as d_err:
            return d_err.payload, {'cls':HttpResponseBadRequest}

    _inner.__name__ = function.__name__
    return _inner

def get_wps_server_or_error(server):
    try:
        return WpsServer.objects.get(identifier=server)
    except WpsServer.DoesNotExist:
        error_msg = 'wps server with identifier {srv} does not exist'.format(srv=server)
        raise DispatchError({'error':error_msg})

def get_process_details_or_error(server, process_code):
    try:
        return server.connection.get_process_details(process_code)
    except WpsError as w_err:
        error_msg = 'an exception was raised by wps {srv} while requesting process details for {prc}'.format(srv=server.identifier, prc=process_code)
        raise DispatchError({'error':error_msg,'code':w_err.code, 'text':w_err.text})

@render_to_json()
def get_wps_server_list(request):
    return WpsServer.objects.dict_objects()

@render_to_json()
@dispatch_errors
def get_process_list(request, server_name):
    return get_wps_server_or_error(server_name).connection.get_process_list()

@render_to_json()
@dispatch_errors
def get_process_details(request, server_name, process_name):
    server = get_wps_server_or_error(server_name)
    return get_process_details_or_error(server, process_name)
