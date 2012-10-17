import urllib2

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

import jsonfield

from .wps import WpsConnection, WpsResultConnection

class WpsServerManager(models.Manager):
    def dict_objects(self): return [wps.to_dict() for wps in super(WpsServerManager, self).get_query_set().all()] 

class WpsServer(models.Model):
    display_name = models.CharField(_("display name"), max_length=50)
    identifier = models.SlugField(_("identifier"), max_length=50, unique=True)
    description = models.TextField(_("description"), blank=True, null=True)
    url = models.URLField(_("wps server url"), max_length=200)

    _connection = None

    @property
    def connection(self):
        if self._connection is None:
            self._connection = WpsConnection(self.url)
        return self._connection

    def to_dict(self):
        return {'display_name':self.display_name,
                'identifier':self.identifier,
                'description':self.description,
                'url':self.url}

    objects = WpsServerManager()

    class Meta:
        verbose_name = _("wps server")
        verbose_name_plural = _("wps servers")

    def __str__(self):
        return self.display_name

class ProcessManager(models.Manager):
    def to_update(self):
        return super(ProcessManager, self).get_query_set().filter(
                Q(status='accepted') | Q(status='noup') |
                Q(status='paused')   | Q(status='started'))

    def by_status(self, status):
        return super(ProcessManager,
                self).get_query_set().filter(status=status)

    def by_user(self, user):
        return super(ProcessManager,
                self).get_query_set().filter(user=user)

    def dict_objects(self):
        return [process.to_dict() for process in super(ProcessManager, self).get_query_set()]

_PROCESS_STATUSES = (
    ('accepted', _("accepted")),
    ('started',_("started")),
    ('paused',_("paused")),
    ('succeeded',_("succeeded")),
    ('failed',_("failed")),
    ('noup', _("cannot update status")),
)

class Process(models.Model):
    user = models.ForeignKey(User, verbose_name=_("user")) # ForeignKey
    server = models.ForeignKey(WpsServer, verbose_name=_("server")) # ForeignKey
    name = models.CharField(_("process name"), max_length=200)

    started_at = models.DateTimeField(_("started at")) # DateTime
    stopped_at = models.DateTimeField(_("stopped at"), blank=True, null=True) # DateTime

    status = models.CharField(_("status"), choices=_PROCESS_STATUSES, max_length=200)

    polling_url = models.URLField(_("polling url"), max_length=200)
    inputs = jsonfield.JSONField(_("inputs"))
    outputs = jsonfield.JSONField(_("outputs"), null=True, blank=True)
    
    _connection = None

    @property
    def connection(self):
        if self._connection is None:
            self._connection = WpsResultConnection(self.polling_url)
        return self._connection

    def poll_and_update(self):
        # If the process has succeeded or failed do not poll. 
        if self.status in ('succeeded', 'failed'):
            return

        try:
            status, payload = self.connection.get_polling_status()
        except IOError: 
            status='noup'
        except urllib2.URLError:
            status='noup'
        
        self.status = status
        self.outputs = payload
        super(Process,self).save()

    def to_dict(self):
        stopped_at = self.stopped_at.isoformat() if self.stopped_at is not None else ""
        return {'server':self.server.identifier,
                'name':self.name,
                'started_at':self.started_at.isoformat(),
                'stopped_at':stopped_at,
                'status':self.status,
                'inputs':self.inputs,
                'outputs':self.outputs,} 

    objects = ProcessManager()

    def __str__(self):
        return "[%s] %s: %s" % (self.started_at.isoformat(), self.name,
                self.user.username)

    class Meta:
        verbose_name = _("process")
        verbose_name_plural = _("processes")
