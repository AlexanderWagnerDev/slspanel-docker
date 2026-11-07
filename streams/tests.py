import os
from unittest.mock import Mock, patch

from django.conf import settings as django_settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, RequestFactory, TestCase, override_settings
from django.utils import translation

from slspanel import settings as project_settings


class CreateUserCommandTests(TestCase):
    """Regression tests for the environment-driven operator account."""

    def setUp(self):
        User.objects.all().delete()

    def _run_with_env(self, **values):
        env = {key: value for key, value in os.environ.items() if key in {"DJANGO_SECRET_KEY", "LANG", "TZ"}}
        env.update(values)
        with patch.dict(os.environ, env, clear=True):
            call_command("create_user")

    def test_configured_username_and_password_create_expected_user(self):
        self._run_with_env(
            REQUIRE_LOGIN="True",
            USERNAME="alice",
            PASSWORD="s3cret",
        )

        self.assertTrue(User.objects.filter(username="alice").exists())
        self.assertFalse(User.objects.filter(username="admin").exists())
        self.assertTrue(User.objects.get(username="alice").check_password("s3cret"))

    def test_existing_user_password_is_updated(self):
        User.objects.create_superuser(username="alice", email="", password="old-password")

        self._run_with_env(
            REQUIRE_LOGIN="True",
            USERNAME="alice",
            PASSWORD="new-password",
        )

        user = User.objects.get(username="alice")
        self.assertTrue(user.check_password("new-password"))
        self.assertFalse(user.check_password("old-password"))

    def test_login_disabled_does_not_create_user(self):
        self._run_with_env(
            REQUIRE_LOGIN="False",
            USERNAME="alice",
            PASSWORD="s3cret",
        )

        self.assertFalse(User.objects.exists())

    def test_login_enabled_without_password_fails_closed(self):
        with self.assertRaises(CommandError):
            self._run_with_env(REQUIRE_LOGIN="True", USERNAME="alice")

        self.assertFalse(User.objects.exists())

    def test_example_password_fails_closed(self):
        with self.assertRaises(CommandError):
            self._run_with_env(REQUIRE_LOGIN="True", USERNAME="alice", PASSWORD="password")

        self.assertFalse(User.objects.exists())

    def test_legacy_default_password_account_is_deactivated(self):
        legacy = User.objects.create_superuser(username="admin", email="", password="password")

        self._run_with_env(
            REQUIRE_LOGIN="True",
            USERNAME="operator",
            PASSWORD="strong-password",
        )

        legacy.refresh_from_db()
        self.assertFalse(legacy.is_active)
        self.assertTrue(User.objects.get(username="operator").is_active)

    def test_default_require_login_matches_settings(self):
        self.assertFalse(project_settings.REQUIRE_LOGIN)
        self._run_with_env(USERNAME="alice", PASSWORD="s3cret")

        self.assertFalse(User.objects.exists())

    def test_legacy_web_credentials_are_supported(self):
        self._run_with_env(
            REQUIRE_LOGIN="True",
            WEB_USERNAME="legacy",
            WEB_PASSWORD="legacy-password",
        )

        user = User.objects.get(username="legacy")
        self.assertTrue(user.check_password("legacy-password"))

    def test_documented_credentials_take_precedence_over_legacy_names(self):
        self._run_with_env(
            REQUIRE_LOGIN="True",
            USERNAME="documented",
            PASSWORD="documented-password",
            WEB_USERNAME="legacy",
            WEB_PASSWORD="legacy-password",
        )

        self.assertTrue(User.objects.filter(username="documented").exists())
        self.assertFalse(User.objects.filter(username="legacy").exists())


class LanguageConfigurationTests(TestCase):
    """Unsupported process locales must not prevent the application from starting."""

    def test_language_normalization_accepts_documented_and_common_values(self):
        cases = {
            "en": "en",
            "de": "de",
            "DE": "de",
            "de_DE.UTF-8": "de",
            "en_US.UTF-8": "en",
            "C.UTF-8": "en",
            "POSIX": "en",
            "fr_FR.UTF-8": "en",
            "": "en",
            None: "en",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(project_settings.normalize_language_code(raw), expected)

    def test_middleware_uses_configured_language_not_raw_environment(self):
        from slspanel.middlewares import ForceEnvLanguageMiddleware

        with patch.dict(os.environ, {"LANG": "en"}):
            with override_settings(LANGUAGE_CODE="de"):
                middleware = ForceEnvLanguageMiddleware(
                    lambda request: __import__("django.http", fromlist=["HttpResponse"]).HttpResponse(
                        translation.get_language()
                    )
                )
                response = middleware(RequestFactory().get("/"))

        self.assertEqual(response.content.decode(), "de")

    @override_settings(LANGUAGE_CODE="de")
    def test_root_redirect_uses_configured_language(self):
        response = Client().get("/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/de/")


class IndexTemplateTests(TestCase):
    """The copied statistics URL must use the configured statistics host."""

    @override_settings(
        REQUIRE_LOGIN=False,
        SLS_DOMAIN_IP="stream.example",
        SLS_STATS_DOMAIN_IP="stats.example",
        SLS_STATS_PORT=8789,
        SLS_STATS_SCHEME="https",
        SRT_PUBLISH_PORT=4001,
        SRT_PLAYER_PORT=4000,
        SRTLA_PUBLISH_PORT=5000,
    )
    def test_statistics_urls_use_statistics_domain(self):
        entries = [{"publisher": "pub", "player": "play", "description": "desc"}]
        with patch("streams.views._fetch_stream_entries", return_value=entries):
            with translation.override("en"):
                response = Client().get("/en/")

        content = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn("https://stats.example:8789/stats/play", content)
        self.assertNotIn("https://stream.example:8789/stats/play", content)
        self.assertIn("srt://stream.example:4001?streamid=pub", content)
        self.assertIn("srt://stream.example:4000?streamid=play", content)

    @override_settings(REQUIRE_LOGIN=False)
    def test_index_surfaces_stream_fetch_failure(self):
        with patch("streams.views._fetch_stream_entries", return_value=None):
            with translation.override("en"):
                response = Client().get("/en/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Failed to fetch streams from the SLS API.")

    @override_settings(
        REQUIRE_LOGIN=False,
        SLS_DOMAIN_IP="stream.example",
        SLS_STATS_DOMAIN_IP="",
        SLS_STATS_PORT=8789,
        SLS_STATS_SCHEME="http",
    )
    def test_empty_statistics_domain_falls_back_to_stream_domain(self):
        entries = [{"publisher": "pub", "player": "play", "description": "desc"}]
        with patch("streams.views._fetch_stream_entries", return_value=entries):
            with translation.override("en"):
                response = Client().get("/en/")

        self.assertContains(response, "http://stream.example:8789/stats/play")

    @override_settings(REQUIRE_LOGIN=False)
    def test_mobile_viewport_is_declared(self):
        with patch("streams.views._fetch_stream_entries", return_value=[]):
            with translation.override("en"):
                response = Client().get("/en/")

        self.assertContains(
            response,
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
        )
        self.assertContains(response, 'data-bs-theme="dark"')


class InitConfigTests(TestCase):
    """The persisted configuration must use the normalized Django language."""

    @override_settings(LANGUAGE_CODE="de")
    def test_initconfig_uses_normalized_language(self):
        from streams.models import Configuration

        call_command("initconfig")

        self.assertEqual(Configuration.objects.get(id=1).language, "de")


class SessionLifecycleTests(TestCase):
    """Logout must revoke the session, not only clear the browser cookie."""

    @override_settings(REQUIRE_LOGIN=True)
    def test_logout_revokes_replayed_session_cookie(self):
        User.objects.create_superuser(username="alice", email="", password="pw")
        client = Client()
        self.assertTrue(client.login(username="alice", password="pw"))
        session_cookie = client.cookies[django_settings.SESSION_COOKIE_NAME].value

        self.assertEqual(client.get("/en/logout/").status_code, 302)

        replay = Client()
        replay.cookies[django_settings.SESSION_COOKIE_NAME] = session_cookie
        response = replay.get("/en/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/en/login/", response.url)


class InputValidationTests(TestCase):
    """Security regression tests for paths and keys that reach the SLS API."""

    def test_stream_key_rejects_trailing_newline(self):
        from streams.views import _is_valid_stream_key

        self.assertFalse(_is_valid_stream_key("play\n"))

    def test_endpoint_rejects_trailing_newline(self):
        from streams.views import _is_safe_endpoint

        self.assertFalse(_is_safe_endpoint("/api/stream-ids\n"))

    @override_settings(REQUIRE_LOGIN=False)
    def test_stats_proxy_rejects_non_object_response(self):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = [1, 2]
        with patch("streams.views.requests.get", return_value=response):
            result = Client().get("/en/sls-stats/play_ok/")

        self.assertEqual(result.status_code, 502)
        self.assertEqual(result.json()["status"], "error")

    @override_settings(REQUIRE_LOGIN=False)
    def test_delete_stream_reports_fetch_failure(self):
        with patch("streams.views._fetch_stream_entries", return_value=None):
            response = Client().post("/en/delete-stream/pub/")

        self.assertEqual(response.status_code, 502)

    @override_settings(REQUIRE_LOGIN=False)
    def test_delete_stream_reports_delete_failure(self):
        entries = [{"publisher": "pub", "player": "play"}]
        with patch("streams.views._fetch_stream_entries", return_value=entries):
            with patch("streams.views.call_api", return_value=(429, {})):
                response = Client().post("/en/delete-stream/pub/")

        self.assertEqual(response.status_code, 502)

    @override_settings(REQUIRE_LOGIN=False)
    def test_delete_stream_success_redirects(self):
        entries = [{"publisher": "pub", "player": "play"}]
        with patch("streams.views._fetch_stream_entries", return_value=entries):
            with patch("streams.views.call_api", return_value=(200, {})):
                response = Client().post("/en/delete-stream/pub/")

        self.assertEqual(response.status_code, 302)

    @override_settings(REQUIRE_LOGIN=False)
    def test_delete_player_reports_api_failure(self):
        with patch("streams.views.call_api", return_value=(403, {})):
            response = Client().post("/en/delete-player/play/")

        self.assertEqual(response.status_code, 502)

    @override_settings(REQUIRE_LOGIN=False)
    def test_delete_player_accepts_not_found(self):
        with patch("streams.views.call_api", return_value=(404, {})):
            response = Client().post("/en/delete-player/play/")

        self.assertEqual(response.status_code, 302)

    @override_settings(REQUIRE_LOGIN=False)
    def test_stats_rejects_traversal_like_player_key(self):
        with translation.override("en"):
            response = Client().get("/en/sls-stats/bad..key/")

        self.assertEqual(response.status_code, 400)

    @override_settings(REQUIRE_LOGIN=False)
    def test_create_stream_rejects_traversal_like_publisher_key(self):
        with translation.override("en"):
            response = Client().post(
                "/en/create-stream/",
                {"publisher": "../escape", "player": "play_ok", "description": ""},
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid stream key")

    @override_settings(REQUIRE_LOGIN=False)
    def test_add_player_rejects_traversal_like_publisher_key(self):
        with translation.override("en"):
            response = Client().post(
                "/en/add-player/",
                {"publisher_key": "../escape", "player_key": "play_ok", "description": ""},
            )

        self.assertEqual(response.status_code, 400)
