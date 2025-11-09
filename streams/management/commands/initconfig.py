from django.core.management.base import BaseCommand
from streams.models import Configuration
import os

class Command(BaseCommand):
    help = "Initial configuration or update from ENV"

    def handle(self, *args, **kwargs):
        lang = os.getenv("LANG", "en")
        conf, created = Configuration.objects.get_or_create(id=1)
        conf.language = lang
        conf.save()
        self.stdout.write(self.style.SUCCESS(f"Config set language to {lang}"))
