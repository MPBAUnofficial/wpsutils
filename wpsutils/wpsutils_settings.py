import os
from django.conf import settings

POLLING_TIMEOUT = getattr(settings, 'POLLING_TIMEOUT', 5)

START_PROCESS = True if getattr(os.environ, 'START_PROCESS', None) == 'True' else False

print os.environ['START_PROCESS']