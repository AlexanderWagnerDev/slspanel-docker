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
            raise CommandError(
                "PASSWORD must not use the example default value; choose a strong password."
            )

        user, created = User.objects.get_or_create(username=username, defaults={"email": ""})
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        # Deactivate legacy accounts that still use the old example password.
        # This covers upgrades where the configured username changed and an
        # old admin/password superuser would otherwise remain usable.
        legacy_users = User.objects.filter(is_superuser=True).exclude(username=username)
        for legacy_user in legacy_users:
            if legacy_user.check_password("password"):
                legacy_user.is_active = False
                legacy_user.save(update_fields=["is_active"])
                self.stdout.write(
                    self.style.WARNING(
                        f"Deactivated legacy default-password account '{legacy_user.username}'."
                    )
                )

        if created:
            self.stdout.write(self.style.SUCCESS(f"User '{username}' was created."))
        else:
            self.stdout.write(self.style.SUCCESS(f"User '{username}' was updated from environment."))
