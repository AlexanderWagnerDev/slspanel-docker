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
                "PASSWORD (or WEB_PASSWORD) must be set when REQUIRE_LOGIN is enabled "
                "(for Docker Compose, set SLS_ADMIN_PASSWORD)."
            )
        if password == "password":
            raise CommandError(
                "PASSWORD must not use the example default value 'password'; choose a strong password "
                "(for Docker Compose, set SLS_ADMIN_PASSWORD)."
            )

        user, created = User.objects.get_or_create(username=username, defaults={"email": ""})
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        # Do not silently alter other accounts. Fail closed when an old
        # superuser still uses the known example password; the operator must
        # change or deactivate it explicitly.
        legacy_users = [
            legacy_user
            for legacy_user in User.objects.filter(is_superuser=True, is_active=True).exclude(username=username)
            if legacy_user.check_password("password")
        ]
        if legacy_users:
            names = ", ".join(sorted(user.username for user in legacy_users))
            raise CommandError(
                "Legacy superuser account(s) still use the example password: "
                f"{names}. Change the password or deactivate them before starting."
            )

        if created:
            self.stdout.write(self.style.SUCCESS(f"User '{username}' was created."))
        else:
            self.stdout.write(self.style.SUCCESS(f"User '{username}' was updated from environment."))
