from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
import os


class Command(BaseCommand):
    help = "Create or update the operator user from ENV"

    def handle(self, *args, **kwargs):
        require_login = os.getenv('REQUIRE_LOGIN', 'False').lower() in ['true', '1', 'yes']
        if not require_login:
            self.stdout.write(self.style.WARNING("Login is disabled via REQUIRE_LOGIN. No user will be created."))
            return

        # USERNAME/PASSWORD are the documented names. Keep the older WEB_* names
        # as a compatibility fallback for existing deployments.
        username = os.getenv("USERNAME") or os.getenv("WEB_USERNAME") or "admin"
        password = os.getenv("PASSWORD") or os.getenv("WEB_PASSWORD")
        if not password:
            raise CommandError(
                "PASSWORD (or WEB_PASSWORD) must be set when REQUIRE_LOGIN is enabled."
            )
        if password == "password":
            self.stdout.write(
                self.style.WARNING("The example password is in use; change PASSWORD before exposing the panel.")
            )

        user, created = User.objects.get_or_create(username=username, defaults={"email": ""})
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"User '{username}' was created."))
        else:
            self.stdout.write(self.style.SUCCESS(f"User '{username}' was updated from environment."))
