import logging
from django.core.management.base import BaseCommand
from ...models import Process

logger = logging.getLogger('wpsutils.management')

class Command(BaseCommand):
    help = 'Polls and updates status for each wps process.'

    def handle(self, *args, **kwargs):
        for proc in Process.objects.to_update():
            proc.poll_and_update()


