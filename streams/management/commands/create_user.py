from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os

class Command(BaseCommand):
    help = "Erstellt User basierend auf ENV"

    def handle(self, *args, **kwargs):
        username = os.getenv("WEB_USERNAME", "admin")
        password = os.getenv("WEB_PASSWORD", "password")
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email="", password=password)
            self.stdout.write(self.style.SUCCESS(f"User '{username}' wurde erstellt."))
        else:
            self.stdout.write(f"User '{username}' existiert bereits.")