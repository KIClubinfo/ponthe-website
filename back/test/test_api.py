import os
import shutil
from unittest import mock

from api.models import Gallery, Year
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

PUBLIC = Gallery.Visibility.PUBLIC
SCHOOL = Gallery.Visibility.SCHOOL
PRIVATE = Gallery.Visibility.PRIVATE


def post_json(client, url, data):
    return client.post(url, data, content_type="application/json")


class GalleryAccessTest(TestCase):
    """Who may open a gallery, list its pictures and fetch its files."""

    # (visibility, user) -> allowed. `None` is a visitor who is not logged in.
    EXPECTED = {
        (PUBLIC, None): True,
        (PUBLIC, "student"): True,
        (PUBLIC, "staff"): True,
        (PUBLIC, "superuser"): True,
        (PUBLIC, "root"): True,
        (SCHOOL, None): False,
        (SCHOOL, "student"): True,
        (SCHOOL, "staff"): True,
        (SCHOOL, "superuser"): True,
        (SCHOOL, "root"): True,
        (PRIVATE, None): False,
        (PRIVATE, "student"): False,
        (PRIVATE, "staff"): True,
        (PRIVATE, "superuser"): True,
        (PRIVATE, "root"): True,
    }

    @classmethod
    def setUpTestData(cls):
        year = Year.objects.create(name="2026-2027")
        cls.slugs = {}
        for index, visibility in enumerate((PUBLIC, SCHOOL, PRIVATE)):
            gallery = Gallery.objects.create(
                name=f"Gallery {index}",
                slug=f"gallery-{index}",
                description="",
                visibility=visibility,
                year=year,
            )
            cls.slugs[visibility] = gallery.slug
        cls.users = {
            "student": User.objects.create_user("student"),
            "staff": User.objects.create_user("staff", is_staff=True),
            "superuser": User.objects.create_superuser("superuser"),
            # A superuser who is not staff: there is one in production.
            "root": User.objects.create_user("root", is_superuser=True),
        }

    def each_case(self):
        for (visibility, who), allowed in self.EXPECTED.items():
            if who:
                self.client.force_login(self.users[who])
            else:
                self.client.logout()
            with self.subTest(visibility=visibility, user=who):
                yield self.slugs[visibility], 200 if allowed else 403

    def test_gallery(self):
        for slug, status in self.each_case():
            response = post_json(self.client, "/api/gallery/", {"slug": slug})
            self.assertEqual(response.status_code, status)

    def test_picture_list(self):
        for slug, status in self.each_case():
            response = post_json(self.client, "/api/gallery/pics/", {"slug": slug})
            self.assertEqual(response.status_code, status)

    def test_files(self):
        for slug, status in self.each_case():
            response = self.client.get(f"/media/{slug}/uploads/picture.jpg")
            self.assertEqual(response.status_code, status)
            if status == 200:
                self.assertEqual(
                    response["X-Accel-Redirect"],
                    f"/protected/{slug}/uploads/picture.jpg",
                )

    def test_debug_mode_serves_the_files_behind_the_same_check(self):
        public, private = self.slugs[PUBLIC], self.slugs[PRIVATE]
        for slug in (public, private, ".corbeille"):
            folder = os.path.join(settings.MEDIA_ROOT, slug, "uploads")
            os.makedirs(folder, exist_ok=True)
            self.addCleanup(shutil.rmtree, os.path.dirname(folder), ignore_errors=True)
            with open(os.path.join(folder, "picture.jpg"), "wb") as f:
                f.write(b"picture of " + slug.encode())

        with override_settings(DEBUG=True):
            response = self.client.get(f"/media/{public}/uploads/picture.jpg")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                b"".join(response.streaming_content), b"picture of " + public.encode()
            )
            # Not logged in: neither a private gallery nor what was deleted.
            for slug in (private, ".corbeille"):
                response = self.client.get(f"/media/{slug}/uploads/picture.jpg")
                self.assertEqual(response.status_code, 403)

    def test_a_path_cannot_leave_the_gallery_it_was_checked_against(self):
        public, private = self.slugs[PUBLIC], self.slugs[PRIVATE]
        for path in (
            f"{public}/../{private}/uploads/picture.jpg",
            f"{public}/./uploads/picture.jpg",
            f"{public}//uploads/picture.jpg",
            f"{public}/uploads/",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(f"/media/{path}").status_code, 403)

    def test_file_names_are_escaped_for_nginx(self):
        slug = self.slugs[PUBLIC]
        response = self.client.get(f"/media/{slug}/uploads/été 100%25 %3F.jpg")
        self.assertEqual(
            response["X-Accel-Redirect"],
            f"/protected/{slug}/uploads/%C3%A9t%C3%A9%20100%25%20%3F.jpg",
        )

    def test_unknown_gallery(self):
        self.client.force_login(self.users["superuser"])
        for url in ("/api/gallery/", "/api/gallery/pics/"):
            self.assertEqual(
                post_json(self.client, url, {"slug": "nope"}).status_code, 404
            )
            self.assertEqual(post_json(self.client, url, {}).status_code, 404)
        self.assertEqual(self.client.get("/media/nope/uploads/a.jpg").status_code, 403)


class ManagementRoutesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gallery = Gallery.objects.create(
            name="Gala",
            slug="gala",
            description="",
            year=Year.objects.create(name="2026-2027"),
        )
        cls.student = User.objects.create_user("student")
        cls.staff = User.objects.create_user("staff", is_staff=True)

    def test_removed_routes_are_gone(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get("/api/import/").status_code, 404)
        self.assertEqual(self.client.put("/api/gallery/upload/").status_code, 404)
        self.assertEqual(self.client.get("/api/associated_pics/").status_code, 404)

    def test_visibility_must_be_a_known_value(self):
        self.client.force_login(self.staff)
        url = "/api/gallery/change_visibility/"
        response = post_json(self.client, url, {"slug": "gala", "visibility": "open"})
        self.assertEqual(response.status_code, 400)
        self.gallery.refresh_from_db()
        self.assertEqual(self.gallery.visibility, PRIVATE)

        response = post_json(self.client, url, {"slug": "gala", "visibility": SCHOOL})
        self.assertEqual(response.status_code, 200)
        self.gallery.refresh_from_db()
        self.assertEqual(self.gallery.visibility, SCHOOL)

    def test_view_must_be_a_known_value(self):
        self.client.force_login(self.staff)
        url = "/api/gallery/change_view/"
        response = post_json(self.client, url, {"slug": "gala", "view": "poster"})
        self.assertEqual(response.status_code, 400)
        response = post_json(self.client, url, {"slug": "gala", "view": "exposition"})
        self.assertEqual(response.status_code, 200)

    def test_rerunning_an_import_takes_a_gallery_not_a_path(self):
        routes = {
            "/api/gallery/gen_thumb": "galerie.loader.generate_thumbnails.delay",
            "/api/gallery/load": "galerie.loader.load_folder_into_gallery.delay",
        }
        for url, task in routes.items():
            with self.subTest(url=url), mock.patch(task) as delay:
                self.client.force_login(self.student)
                self.assertEqual(
                    post_json(self.client, url, {"slug": "gala"}).status_code, 403
                )

                self.client.force_login(self.staff)
                response = post_json(self.client, url, {"slug": "../../etc"})
                self.assertEqual(response.status_code, 404)
                delay.assert_not_called()

                self.assertEqual(
                    post_json(self.client, url, {"slug": "gala"}).status_code, 200
                )
                delay.assert_called_once_with("gala")


class ApiDefaultsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user("staff", password="secret", is_staff=True)
        cls.student = User.objects.create_user("student")

    def test_a_route_without_declared_permissions_is_for_managers(self):
        self.assertEqual(self.client.get("/api/").status_code, 403)
        self.client.force_login(self.student)
        self.assertEqual(self.client.get("/api/").status_code, 403)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get("/api/").status_code, 200)

    def test_public_routes_stay_public(self):
        for url in (
            "/api/get_view",
            "/api/years/",
            "/api/galleries/",
            "/api/expositions/",
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_basic_authentication_is_not_accepted(self):
        import base64

        credentials = base64.b64encode(b"staff:secret").decode()
        response = self.client.get("/api/", HTTP_AUTHORIZATION=f"Basic {credentials}")
        self.assertEqual(response.status_code, 403)


class ManagerRoleTest(TestCase):
    """One role runs the galleries: staff or superuser, on the pages and the API."""

    @classmethod
    def setUpTestData(cls):
        year = Year.objects.create(name="2026-2027")
        Gallery.objects.create(name="Gala", slug="gala", description="", year=year)
        cls.users = {
            "student": User.objects.create_user("student"),
            "staff": User.objects.create_user("staff", is_staff=True),
            "root": User.objects.create_user("root", is_superuser=True),
        }

    def each_user(self):
        for who, manages in (("student", False), ("staff", True), ("root", True)):
            self.client.force_login(self.users[who])
            with self.subTest(user=who):
                yield manages

    def test_management_pages(self):
        for manages in self.each_user():
            for url in ("/gestion/", "/gestion/gallery/gala"):
                response = self.client.get(url)
                if manages:
                    self.assertEqual(response.status_code, 200)
                else:
                    self.assertRedirects(
                        response, f"/login/?next={url}", fetch_redirect_response=False
                    )

    def test_management_api(self):
        for manages in self.each_user():
            response = post_json(
                self.client,
                "/api/gallery/change_view/",
                {"slug": "gala", "view": "galerie"},
            )
            self.assertEqual(response.status_code, 200 if manages else 403)

    def test_private_galleries_are_listed_for_managers_only(self):
        for manages in self.each_user():
            slugs = [g["slug"] for g in self.client.get("/api/get_view").json()]
            self.assertEqual(slugs, ["gala"] if manages else [])

    def test_the_menu_shows_the_management_link_to_managers(self):
        for manages in self.each_user():
            page = self.client.get("/galleries/").content.decode()
            self.assertIn(f"is_staff = {'true' if manages else 'false'};", page)
