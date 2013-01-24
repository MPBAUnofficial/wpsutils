from django.conf.urls import patterns, url

urlpatterns = patterns('wpsutils.views',
    url(r'server/list/$',
        'get_wps_server_list', name='wps-server-list'),
    url(r'process/list/(?P<server_name>[-\w]+)/$', 
        'get_process_list', name='process-list'),
    url(r'process/details/(?P<server_name>[-\w]+)/(?P<process_name>[_.\w]+)/$',
        'get_process_details', name='process-details'),
    url(r'process/run/(?P<server_name>[-\w]+)/(?P<process_name>[_.\w]+)/$',
        'run_process', name='run-process'),
    url(r'process/my/', 'my_process_list', name='my-process-list'),
)
