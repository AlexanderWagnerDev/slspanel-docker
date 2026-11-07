from django.conf import settings
from django.core.management.base import BaseCommand
from streams.models import Configuration


class Command(BaseCommand):
    help = "Initial configuration or update from ENV"

    def handle(self, *args, **kwargs):
        conf, _ = Configuration.objects.get_or_create(id=1)
        conf.language = settings.LANGUAGE_CODE
        conf.save()
        self.stdout.write(self.style.SUCCESS(f"Config set language to {conf.language}"))
