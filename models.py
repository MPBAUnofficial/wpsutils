from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

import jsonfield

from wps import WpsConnection, WpsResultConnection

class WpsServerManager(models.Manager):
    def dict_objects(self):
        return [wps.to_dict() for wps in super(WpsServerManager, self).get_query_set().all()] 

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
    def completed(self):
        return super(ProcessManager,
                self).get_query_set().filter(stopped_at__isnull=False)

    def running(self):
        return super(ProcessManager,
                self).get_query_set().filter(stopped_at__isnull=True)

    def with_errors(self):
        return super(ProcessManager,
                self).get_query_set().filter(with_errors=True)

class Process(models.Model):
    user = models.ForeignKey(User, verbose_name=_("user")) # ForeignKey
    server = models.ForeignKey(WpsServer, verbose_name=_("server")) # ForeignKey

    started_at = models.DateTimeField(_("started at")) # DateTime
    stopped_at = models.DateTimeField(_("stopped at"), blank=True, null=True) # DateTime

    with_errors = models.NullBooleanField(_("with errors"), default=None)

    polling_url = models.URLField(_("polling url"), max_length=200)
    inputs = jsonfield.JSONField(_("inputs"))
    outputs = jsonfield.JSONField(_("outputs"))
    
    _connection = None

    @property
    def connection(self):
        if self._connection is None:
            self._connection = WpsResultConnection(self.polling_url)
        return self._connection

    def to_dict(self):
        return {'server':self.server.identifier,
                'started_at':self.started_at,
                'stopped_at':self.stopped_at,
                'with_errors':self.with_errors,} 
        #TODO: finish up here
        #TODO: add process identifier (query from connection or save ?) 
        #TODO: 

    objects = ProcessManager()

    class Meta:
        verbose_name = _("process")
        verbose_name_plural = _("processes")
