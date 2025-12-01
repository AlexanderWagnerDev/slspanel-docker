from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os

class Command(BaseCommand):
    help = "Create User from ENV"

    def handle(self, *args, **kwargs):
        require_login = os.getenv('REQUIRE_LOGIN', 'True').lower() in ['true', '1', 'yes']
        if not require_login:
            self.stdout.write(self.style.WARNING("Login is disabled via REQUIRE_LOGIN. No user will be created."))
            return

        username = os.getenv("WEB_USERNAME", "admin")
        password = os.getenv("WEB_PASSWORD", "password")
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email="", password=password)
            self.stdout.write(self.style.SUCCESS(f"User '{username}' was created."))
        else:
            self.stdout.write(f"User '{username}' already exists.")