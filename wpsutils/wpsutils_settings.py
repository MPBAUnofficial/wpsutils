from django.conf import settings

def get(key, default):
    return getattr(settings, key, default)

POLLING_TIMEOUT = get('POLLING_TIMEOUT', 5)

# It can be either True, False or Null and they all have different meaning ...
# True : thread is running
# False : thread not started
# None : thread should not start : useful when syncing db ...
THREAD_STARTED = False
