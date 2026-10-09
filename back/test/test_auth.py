from unittest import mock

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from galerie.auth import CASBackend


def cas_answers(username, **attributes):
    """Make the CAS validate any ticket as `username`, with these attributes."""
    client = mock.Mock()
    client.verify_ticket.return_value = (username, attributes or None, None)
    return mock.patch("galerie.auth.get_cas_client", return_value=client)


def cas_login():
    return CASBackend().authenticate(None, ticket="ST-1", service="https://x/")


class CASBackendTest(TestCase):
    def test_known_username(self):
        account = User.objects.create_user("j.dupont", first_name="Jeanne")
        with cas_answers(
            "j.dupont", mail="j.dupont@enpc.fr", givenName="J", sn="Dupont"
        ):
            user = cas_login()

        self.assertEqual(user, account)
        user.refresh_from_db()
        # Blanks are filled, what was already there is kept.
        self.assertEqual(
            (user.first_name, user.last_name, user.email),
            ("Jeanne", "Dupont", "j.dupont@enpc.fr"),
        )

    def test_unknown_username_is_matched_on_the_address(self):
        admin = User.objects.create_user(
            "admin-ponthe", email="Jeanne.Dupont@enpc.fr", is_staff=True
        )
        with cas_answers("j.dupont", mail="jeanne.dupont@enpc.fr"):
            user = cas_login()

        self.assertEqual(user, admin)
        self.assertTrue(user.is_staff)
        self.assertEqual(User.objects.count(), 1)

    def test_an_address_shared_by_two_accounts_matches_none(self):
        User.objects.create_user("one", email="shared@enpc.fr")
        User.objects.create_user("two", email="shared@enpc.fr")
        with cas_answers("j.dupont", mail="shared@enpc.fr"), self.assertLogs(
            "galerie.auth", level="WARNING"
        ):
            user = cas_login()

        self.assertEqual(user.username, "j.dupont")
        self.assertEqual(User.objects.count(), 3)

    def test_unknown_person_gets_an_account(self):
        with cas_answers(
            "j.dupont", mail=["j.dupont@enpc.fr", "other@enpc.fr"], sn="Dupont"
        ):
            user = cas_login()

        self.assertEqual(
            (user.username, user.email, user.last_name, user.is_staff),
            ("j.dupont", "j.dupont@enpc.fr", "Dupont", False),
        )

    def test_a_bare_identifier_is_not_an_address(self):
        User.objects.create_user("other", email="j.dupont")
        with cas_answers("j.dupont", mail="j.dupont"):
            user = cas_login()

        self.assertEqual((user.username, user.email), ("j.dupont", ""))

    def test_no_attributes_at_all(self):
        with cas_answers("j.dupont"):
            self.assertEqual(cas_login().username, "j.dupont")

    def test_rejected_ticket(self):
        with cas_answers(None):
            self.assertIsNone(cas_login())
        self.assertEqual(User.objects.count(), 0)

    def test_inactive_account(self):
        User.objects.create_user("j.dupont", is_active=False)
        with cas_answers("j.dupont"):
            self.assertIsNone(cas_login())

    @override_settings(CAS_CREATE_USER=False)
    def test_account_creation_can_be_switched_off(self):
        with cas_answers("j.dupont"):
            self.assertIsNone(cas_login())
        self.assertEqual(User.objects.count(), 0)


class CASLoginViewTest(TestCase):
    @override_settings(
        CAS_SERVER_URL="https://idp.example/cas/", CAS_FORCE_SSL_SERVICE_URL=True
    )
    def test_redirects_to_the_configured_cas_with_an_https_service(self):
        response = self.client.get(reverse("cas_ng_login"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response["Location"].startswith(
                "https://idp.example/cas/login?service=https%3A%2F%2Ftestserver%2Faccounts%2Flogin%2F"
            ),
            response["Location"],
        )

    def test_a_valid_ticket_opens_a_session(self):
        admin = User.objects.create_user("admin-ponthe", email="j.dupont@enpc.fr")
        with cas_answers("j.dupont", mail="j.dupont@enpc.fr"):
            response = self.client.get(reverse("cas_ng_login"), {"ticket": "ST-1"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session["_auth_user_id"], str(admin.pk))


class EmailBackendTest(TestCase):
    def test_two_accounts_with_the_same_address(self):
        User.objects.create_user("one", email="shared@enpc.fr", password="first")
        two = User.objects.create_user("two", email="shared@enpc.fr", password="second")

        self.assertEqual(
            authenticate(username="Shared@enpc.fr", password="second"), two
        )
        self.assertIsNone(authenticate(username="shared@enpc.fr", password="wrong"))


LOCAL_CACHE = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}


@override_settings(CACHES=LOCAL_CACHE, LOGIN_MAX_FAILURES=3)
class LoginLimitTest(TestCase):
    def setUp(self):
        cache.clear()
        User.objects.create_user("jeanne", email="jeanne@enpc.fr", password="right")

    def login(self, password, username="jeanne@enpc.fr"):
        return self.client.post("/login/", {"username": username, "password": password})

    def test_an_account_is_put_on_hold_after_too_many_failures(self):
        for _ in range(3):
            self.assertEqual(self.login("wrong").status_code, 200)
        # Even the right password is refused now, and so is another spelling.
        self.assertEqual(self.login("right").status_code, 429)
        self.assertEqual(self.login("right", " Jeanne@ENPC.fr ").status_code, 429)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_other_accounts_are_not_affected(self):
        User.objects.create_user("paul", email="paul@enpc.fr", password="right")
        for _ in range(3):
            self.login("wrong")
        self.assertEqual(self.login("right", "paul@enpc.fr").status_code, 302)

    def test_a_successful_login_resets_the_count(self):
        self.login("wrong")
        self.login("wrong")
        self.assertEqual(self.login("right").status_code, 302)
        self.client.logout()
        self.login("wrong")
        self.login("wrong")
        self.assertEqual(self.login("right").status_code, 302)

    def test_login_still_works_when_the_cache_is_down(self):
        broken = mock.Mock()
        broken.get.side_effect = broken.add.side_effect = ConnectionError
        broken.incr.side_effect = broken.delete.side_effect = ConnectionError
        with mock.patch("galerie.views.cache", broken), self.assertLogs(
            "galerie.views", level="ERROR"
        ):
            self.assertEqual(self.login("wrong").status_code, 200)
            self.assertEqual(self.login("right").status_code, 302)


class ProxyTest(TestCase):
    @override_settings(
        SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"),
        SECURE_HSTS_SECONDS=3600,
    )
    def test_https_is_recognised_behind_nginx(self):
        plain = self.client.get("/")
        self.assertNotIn("Strict-Transport-Security", plain)
        forwarded = self.client.get("/", HTTP_X_FORWARDED_PROTO="https")
        self.assertEqual(forwarded["Strict-Transport-Security"], "max-age=3600")


class AdminLoginTest(TestCase):
    """The admin has no login form of its own: the site's is the one with a limit."""

    def test_visitors_are_sent_to_the_site_login(self):
        for url in (
            "/admin/",
            "/admin/login/",
            "/admin/login/?next=/admin/api/gallery/",
        ):
            with self.subTest(url=url):
                response = self.client.get(url, follow=True)
                self.assertEqual(
                    response.redirect_chain[-1][0].split("?")[0], "/login/"
                )

    def test_the_admin_form_does_not_try_passwords(self):
        User.objects.create_user("chef", password="right", is_staff=True)
        response = self.client.post(
            "/admin/login/", {"username": "chef", "password": "right"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_staff_reach_the_admin_once_logged_in(self):
        self.client.force_login(User.objects.create_user("chef", is_staff=True))
        self.assertRedirects(self.client.get("/admin/login/"), "/admin/")
        self.assertEqual(self.client.get("/admin/").status_code, 200)

    def test_other_accounts_are_refused_without_a_redirect_loop(self):
        self.client.force_login(User.objects.create_user("student"))
        response = self.client.get("/admin/", follow=True)
        self.assertEqual(response.status_code, 403)
        self.assertLessEqual(len(response.redirect_chain), 1)


class EnvFlagTest(TestCase):
    def test_debug_has_to_be_asked_for(self):
        from galerie.settings import env_flag

        for value, expected in (
            ("True", True),
            ("true", True),
            ("1", True),
            ("False", False),
            ("false", False),
            ("0", False),
            ("no", False),
            ("", False),
            ("Flase", False),
        ):
            with self.subTest(value=value), mock.patch.dict(
                "os.environ", {"SOME_FLAG": value}
            ):
                self.assertIs(env_flag("SOME_FLAG"), expected)
        with mock.patch.dict("os.environ", clear=True):
            self.assertIs(env_flag("SOME_FLAG"), False)
