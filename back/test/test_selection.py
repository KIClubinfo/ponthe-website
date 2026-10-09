import io
import os
import shutil
import zipfile

from api.models import File, Gallery, Report, Year
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from galerie import loader
from galerie.loader import gallery_path

from .test_api import post_json

SLUG = "select-public"
PRIVATE_SLUG = "select-private"


def zip_of_response(response):
    """The archive is streamed from a temporary file, not held in memory."""
    return zipfile.ZipFile(io.BytesIO(b"".join(response.streaming_content)))


class DownloadPicsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        year = Year.objects.create(name="2026-2027")
        cls.gallery = Gallery.objects.create(
            name="Sélection",
            slug=SLUG,
            description="",
            visibility=Gallery.Visibility.PUBLIC,
            year=year,
        )
        for name in ("picture.jpg", "other.jpg", "untouched.jpg"):
            File.objects.create(
                file_name=os.path.splitext(name)[0],
                file_extension="jpg",
                file_full_name=name,
                link=f"/media/{SLUG}",
                gallery=cls.gallery,
            )
        cls.student = User.objects.create_user("student")
        cls.manager = User.objects.create_user("manager", is_staff=True)

    def setUp(self):
        # download_pics lit les fichiers sur le disque : on en pose des faux.
        os.makedirs(gallery_path(SLUG, "uploads"), exist_ok=True)
        for name in ("picture.jpg", "other.jpg", "untouched.jpg"):
            with open(gallery_path(SLUG, "uploads", name), "wb") as f:
                f.write(b"fake image bytes")

    def tearDown(self):
        shutil.rmtree(gallery_path(SLUG), ignore_errors=True)

    def download(self, slug=SLUG, names=("picture.jpg", "other.jpg"), who=None):
        if who is not None:
            self.client.force_login(who)
        return post_json(
            self.client,
            "/api/gallery/pics/download/",
            {"slug": slug, "file_full_names": list(names)},
        )

    def test_zip_contains_selected_pictures(self):
        response = self.download()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        archive = zip_of_response(response)
        self.assertEqual(sorted(archive.namelist()), ["other.jpg", "picture.jpg"])

    def test_unknown_gallery_returns_404(self):
        response = self.download(slug="does-not-exist")
        self.assertEqual(response.status_code, 404)

    def test_empty_selection_returns_400(self):
        response = self.download(names=())
        self.assertEqual(response.status_code, 400)

    def test_selection_of_unknown_pictures_returns_404(self):
        response = self.download(names=("ghost.jpg",))
        self.assertEqual(response.status_code, 404)

    def test_unknown_names_are_ignored(self):
        response = self.download(names=("picture.jpg", "ghost.jpg"))
        self.assertEqual(response.status_code, 200)
        archive = zip_of_response(response)
        self.assertEqual(archive.namelist(), ["picture.jpg"])

    def test_missing_disk_file_is_omitted_from_zip(self):
        os.remove(gallery_path(SLUG, "uploads", "other.jpg"))
        response = self.download()
        self.assertEqual(response.status_code, 200)
        archive = zip_of_response(response)
        self.assertEqual(archive.namelist(), ["picture.jpg"])

    def test_names_not_a_list_returns_400(self):
        response = post_json(
            self.client,
            "/api/gallery/pics/download/",
            {"slug": SLUG, "file_full_names": "picture.jpg"},
        )
        self.assertEqual(response.status_code, 400)

    def test_a_name_holding_a_path_is_left_out(self):
        # Cannot come from an import; can be typed in the admin.
        File.objects.create(
            file_full_name="../../picture.jpg",
            link=f"/media/{SLUG}",
            gallery=self.gallery,
        )
        response = self.download(names=("picture.jpg", "../../picture.jpg"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(zip_of_response(response).namelist(), ["picture.jpg"])

    def test_names_that_are_not_strings_return_400(self):
        response = post_json(
            self.client,
            "/api/gallery/pics/download/",
            {"slug": SLUG, "file_full_names": ["picture.jpg", {"a": 1}, ["x"]]},
        )
        self.assertEqual(response.status_code, 400)

    def test_pictures_are_stored_with_their_exact_content(self):
        response = self.download()
        archive = zip_of_response(response)
        self.assertEqual(archive.read("picture.jpg"), b"fake image bytes")
        self.assertEqual(
            {info.compress_type for info in archive.infolist()}, {zipfile.ZIP_STORED}
        )
        self.assertIn("select-public-selection.zip", response["Content-Disposition"])

    @override_settings(DOWNLOAD_MAX_PHOTOS=2)
    def test_a_selection_cannot_exceed_the_number_of_pictures_allowed(self):
        self.assertEqual(self.download().status_code, 200)
        response = self.download(names=("picture.jpg", "other.jpg", "untouched.jpg"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("2 photos", response.data["message"])

    @override_settings(DOWNLOAD_MAX_BYTES=20)
    def test_a_selection_cannot_exceed_the_weight_allowed(self):
        # Each fake picture weighs 16 bytes.
        self.assertEqual(self.download(names=("picture.jpg",)).status_code, 200)
        response = self.download()
        self.assertEqual(response.status_code, 400)
        self.assertIn("trop lourde", response.data["message"])


class DownloadPicsAccessTest(TestCase):
    """Une galerie privée ne se télécharge que si on peut la voir."""

    @classmethod
    def setUpTestData(cls):
        year = Year.objects.create(name="2026-2027")
        cls.private_gallery = Gallery.objects.create(
            name="Sélection privée",
            slug=PRIVATE_SLUG,
            description="",
            visibility=Gallery.Visibility.PRIVATE,
            year=year,
        )
        File.objects.create(
            file_name="picture",
            file_extension="jpg",
            file_full_name="picture.jpg",
            link=f"/media/{PRIVATE_SLUG}",
            gallery=cls.private_gallery,
        )
        cls.student = User.objects.create_user("student")
        cls.manager = User.objects.create_user("manager", is_staff=True)

    def setUp(self):
        os.makedirs(gallery_path(PRIVATE_SLUG, "uploads"), exist_ok=True)
        with open(gallery_path(PRIVATE_SLUG, "uploads", "picture.jpg"), "wb") as f:
            f.write(b"fake image bytes")

    def tearDown(self):
        shutil.rmtree(gallery_path(PRIVATE_SLUG), ignore_errors=True)

    def download(self, who=None):
        if who is not None:
            self.client.force_login(who)
        return post_json(
            self.client,
            "/api/gallery/pics/download/",
            {"slug": PRIVATE_SLUG, "file_full_names": ["picture.jpg"]},
        )

    def test_anonymous_and_student_are_refused(self):
        self.assertEqual(self.download().status_code, 403)
        self.assertEqual(self.download(self.student).status_code, 403)

    def test_manager_can_download(self):
        self.assertEqual(self.download(self.manager).status_code, 200)


class DeletePicsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        year = Year.objects.create(name="2026-2027")
        cls.gallery = Gallery.objects.create(
            name="Sélection delete",
            slug="select-delete",
            description="",
            visibility=Gallery.Visibility.PUBLIC,
            year=year,
        )
        for name in ("picture.jpg", "other.jpg", "untouched.jpg"):
            File.objects.create(
                file_name=os.path.splitext(name)[0],
                file_extension="jpg",
                file_full_name=name,
                link="/media/select-delete",
                gallery=cls.gallery,
            )
        cls.student = User.objects.create_user("student")
        cls.manager = User.objects.create_user("manager", is_staff=True)

    def delete_many(
        self, slug="select-delete", names=("picture.jpg", "other.jpg"), who=None
    ):
        if who is not None:
            self.client.force_login(who)
        return post_json(
            self.client,
            "/api/gallery/pics/delete_many/",
            {"slug": slug, "file_full_names": list(names)},
        )

    def test_manager_deletes_selected_pictures(self):
        response = self.delete_many(who=self.manager)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["deleted"], 2)
        remaining = set(
            File.objects.filter(gallery=self.gallery).values_list(
                "file_full_name", flat=True
            )
        )
        self.assertEqual(remaining, {"untouched.jpg"})

    def test_student_cannot_delete_pictures(self):
        response = self.delete_many(who=self.student)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(File.objects.filter(gallery=self.gallery).count(), 3)

    def test_unknown_gallery_returns_404(self):
        response = self.delete_many(slug="does-not-exist", who=self.manager)
        self.assertEqual(response.status_code, 404)

    def test_empty_selection_returns_400(self):
        response = self.delete_many(names=(), who=self.manager)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(File.objects.filter(gallery=self.gallery).count(), 3)

    def test_deleted_counts_only_pictures_not_reports(self):
        Report.objects.create(
            file=File.objects.get(gallery=self.gallery, file_full_name="picture.jpg"),
            reporter=self.student,
        )
        response = self.delete_many(who=self.manager)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["deleted"], 2)
        self.assertEqual(Report.objects.count(), 0)

    def test_names_not_a_list_returns_400(self):
        self.client.force_login(self.manager)
        response = post_json(
            self.client,
            "/api/gallery/pics/delete_many/",
            {"slug": "select-delete", "file_full_names": "picture.jpg"},
        )
        self.assertEqual(response.status_code, 400)


class DeletedPicturesLeaveTheSiteTest(TestCase):
    """Deleting a picture takes its files with it, and it does not come back."""

    SLUG = "select-files"

    def setUp(self):
        self.gallery = Gallery.objects.create(
            name="Select files",
            slug=self.SLUG,
            description="",
            visibility=Gallery.Visibility.PUBLIC,
            year=Year.objects.create(name="2026-2027"),
        )
        for folder in ("uploads", "thumbnails"):
            os.makedirs(gallery_path(self.SLUG, folder))
            for name in ("gone.jpg", "kept.jpg"):
                with open(gallery_path(self.SLUG, folder, name), "wb") as f:
                    f.write(b"fake image bytes")
        with open(gallery_path(self.SLUG, "uploads", "notes.txt"), "wb") as f:
            f.write(b"never registered")
        loader.load_folder_into_gallery(self.SLUG)
        self.addCleanup(shutil.rmtree, gallery_path(self.SLUG), ignore_errors=True)
        self.addCleanup(shutil.rmtree, self.trash(), ignore_errors=True)
        self.client.force_login(User.objects.create_user("manager", is_staff=True))

    def trash(self, *parts):
        return gallery_path(".corbeille", self.SLUG, "uploads", *parts)

    def names_in_gallery(self):
        files = File.objects.filter(gallery=self.gallery)
        return sorted(files.values_list("file_full_name", flat=True))

    def test_bulk_delete_removes_the_files(self):
        response = post_json(
            self.client,
            "/api/gallery/pics/delete_many/",
            {"slug": self.SLUG, "file_full_names": ["gone.jpg"]},
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            os.listdir(gallery_path(self.SLUG, "thumbnails")), ["kept.jpg"]
        )
        self.assertEqual(
            sorted(os.listdir(gallery_path(self.SLUG, "uploads"))),
            ["kept.jpg", "notes.txt"],
        )
        # The original is kept aside, out of reach of the site.
        with open(self.trash("gone.jpg"), "rb") as f:
            self.assertEqual(f.read(), b"fake image bytes")

    def test_a_deleted_picture_does_not_come_back_with_the_next_import(self):
        post_json(
            self.client,
            "/api/gallery/pics/delete_many/",
            {"slug": self.SLUG, "file_full_names": ["gone.jpg"]},
        )
        loader.load_folder_into_gallery(self.SLUG)
        self.assertEqual(self.names_in_gallery(), ["kept.jpg"])

    def test_single_delete_removes_the_files_too(self):
        response = post_json(
            self.client,
            "/api/gallery/pics/delete/",
            {"name": self.gallery.name, "file_full_name": "gone.jpg"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(os.path.exists(gallery_path(self.SLUG, "uploads", "gone.jpg")))
        self.assertTrue(os.path.exists(self.trash("gone.jpg")))

    def test_deleting_a_gallery_removes_its_folder(self):
        response = post_json(
            self.client, "/api/gallery/delete/", {"name": self.gallery.name}
        )
        self.assertEqual(response.status_code, 200)

        self.assertFalse(os.path.exists(gallery_path(self.SLUG)))
        self.assertEqual(
            sorted(os.listdir(self.trash())), ["gone.jpg", "kept.jpg", "notes.txt"]
        )

    def test_a_gallery_can_be_created_again_under_the_same_name(self):
        new = {"name": self.gallery.name, "description": "Bis", "visibility": "privée"}
        # While it exists, its folder is in the way.
        response = post_json(self.client, "/api/galleries/create/", new)
        self.assertEqual(response.status_code, 400)

        post_json(self.client, "/api/gallery/delete/", {"name": self.gallery.name})
        response = post_json(self.client, "/api/galleries/create/", new)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(os.listdir(gallery_path(self.SLUG, "uploads")), [])
        self.assertEqual(Gallery.objects.filter(slug=self.SLUG).count(), 1)

    def test_a_missing_file_does_not_prevent_the_deletion(self):
        os.remove(gallery_path(self.SLUG, "uploads", "gone.jpg"))
        os.remove(gallery_path(self.SLUG, "thumbnails", "gone.jpg"))
        File.objects.get(gallery=self.gallery, file_full_name="gone.jpg").delete()
        self.assertEqual(self.names_in_gallery(), ["kept.jpg"])
