from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

import jsonfield

from wps import WpsConnection

class WpsServerManager(models.Manager):
    def to_json(self):
        return [wps.to_json() for wps in super(WpsServerManager,
            self).get_query_set().all()]

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

    def to_json(self):
        return {'display_name':self.display_name,
                'identifer':self.identifier,
                'description':self.description,
                'url':self.url}

    objects = WpsServerManager()

    class Meta:
        verbose_name = "wps server"
        verbose_name_plural = "wps Servers"

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
    inputs = jsonfield.JSONField(_("inputs")) # JsonField
    objects = ProcessManager()

    class Meta:
        verbose_name = "process"
        verbose_name_plural = "processes"
