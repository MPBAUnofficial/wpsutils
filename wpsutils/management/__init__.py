from django.db.models.signals import post_syncdb
from .. import models as mymodels
from .. import wpsutils_settings as sett

def no_thread(sender, **kwargs):
    setattr(sett, 'THREAD_STARTED', None)

post_syncdb.connect(no_thread, sender=mymodels)