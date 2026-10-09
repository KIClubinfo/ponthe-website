import io
import os
import shutil
import tempfile
import zipfile
from unittest import mock

from api.models import File, Gallery, Year
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from galerie import loader
from PIL import Image


def jpeg(size=(60, 40)):
    buffer = io.BytesIO()
    Image.new("RGB", size, "teal").save(buffer, "JPEG")
    return buffer.getvalue()


def zip_of(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


class UploadTestCase(TestCase):
    """Galerie « sobriete » avec dossiers media, client connecté, upload AJAX."""

    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media)
        settings = override_settings(MEDIA_ROOT=self.media)
        settings.enable()
        self.addCleanup(settings.disable)

        self.gallery = Gallery.objects.create(
            name="Sobriété",
            slug="sobriete",
            description="",
            year=Year.objects.create(name="2026-2027"),
        )
        os.makedirs(self.path("uploads"))
        os.makedirs(self.path("thumbnails"))
        self.client.force_login(User.objects.create_superuser("admin"))
        self.ajax_headers = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}

    def path(self, *parts):
        return os.path.join(self.media, "sobriete", *parts)

    def upload(self, name, content):
        patches = (
            mock.patch("galerie.loader.generate_thumbnails.delay"),
            mock.patch("galerie.loader.load_folder_into_gallery.delay"),
        )
        with patches[0] as thumbnails, patches[1] as load:
            response = self.client.post(
                "/gestion/gallery/sobriete",
                {"zipfile": SimpleUploadedFile(name, content)},
            )
        return response, thumbnails, load

    def upload_ajax(self, name, content, content_type="application/zip"):
        patches = (
            mock.patch("galerie.loader.generate_thumbnails.delay"),
            mock.patch("galerie.loader.load_folder_into_gallery.delay"),
        )
        with patches[0] as thumbnails, patches[1] as load:
            response = self.client.post(
                "/gestion/gallery/sobriete",
                {"zipfile": SimpleUploadedFile(name, content, content_type)},
                **self.ajax_headers,
            )
        return response, thumbnails, load

    def zips_left(self):
        return [name for name in os.listdir(self.media) if name.endswith(".zip")]


class ImportTest(UploadTestCase):
    def test_zip_name_with_accents_spaces_and_parentheses(self):
        archive = zip_of({"a.jpg": jpeg(), "b.jpg": jpeg()})
        response, thumbnails, load = self.upload("sOBriété 2026 (1).zip", archive)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(sorted(os.listdir(self.path("uploads"))), ["a.jpg", "b.jpg"])
        thumbnails.assert_called_once_with("sobriete")
        load.assert_called_once_with("sobriete")
        self.assertEqual(self.zips_left(), [])

    def test_a_file_that_is_not_a_zip_is_refused_and_removed(self):
        response, thumbnails, load = self.upload("photos.zip", b"not a zip")

        self.assertEqual(response.status_code, 400)
        thumbnails.assert_not_called()
        load.assert_not_called()
        self.assertEqual(self.zips_left(), [])

    def test_unknown_gallery(self):
        response = self.client.post(
            "/gestion/gallery/nope",
            {"zipfile": SimpleUploadedFile("a.zip", zip_of({"a.jpg": jpeg()}))},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.zips_left(), [])

    def fill_uploads(self):
        files = {
            "a.jpg": jpeg(),
            "B.JPG": jpeg((40, 60)),
            "final.v2.png": jpeg(),
            "broken.jpg": b"not a picture",
            "no_extension": jpeg(),
            "notes.txt": b"hello",
            ".DS_Store": b"",
            "._a.jpg": b"",
        }
        for name, content in files.items():
            with open(self.path("uploads", name), "wb") as file:
                file.write(content)
        os.makedirs(self.path("uploads", "__MACOSX"))
        os.makedirs(self.path("uploads", "folder.jpg"))

    def test_only_pictures_are_registered_and_only_once(self):
        self.fill_uploads()
        loader.load_folder_into_gallery("sobriete")
        loader.load_folder_into_gallery("sobriete")

        rows = File.objects.filter(gallery=self.gallery).order_by("id")
        self.assertEqual(
            [(f.file_full_name, f.file_name, f.file_extension) for f in rows],
            [
                ("B.JPG", "B", "JPG"),
                ("a.jpg", "a", "jpg"),
                ("broken.jpg", "broken", "jpg"),
                ("final.v2.png", "final.v2", "png"),
            ],
        )
        self.assertEqual({f.link for f in rows}, {"/media/sobriete"})

    def test_one_unreadable_picture_does_not_stop_the_thumbnails(self):
        self.fill_uploads()
        with self.assertLogs("galerie.loader", level="ERROR"):
            loader.generate_thumbnails("sobriete")

        self.assertEqual(
            sorted(os.listdir(self.path("thumbnails"))),
            ["B.JPG", "a.jpg", "final.v2.png"],
        )

    def test_gallery_deleted_before_the_worker_runs(self):
        self.gallery.delete()
        with self.assertLogs("galerie.loader", level="WARNING"):
            loader.load_folder_into_gallery("sobriete")


class UploadErrorMessagesTest(UploadTestCase):
    """L'upload AJAX retourne du JSON avec un message d'erreur clair."""

    def test_ajax_not_a_zip_returns_json_error(self):
        response, thumbnails, load = self.upload_ajax("photos.zip", b"not a zip")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("zip", data["message"].lower())
        thumbnails.assert_not_called()
        load.assert_not_called()

    def test_ajax_empty_file_returns_json_error(self):
        response, thumbnails, load = self.upload_ajax("empty.zip", b"")

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("vide", data["message"].lower())
        thumbnails.assert_not_called()
        load.assert_not_called()

    def test_ajax_wrong_extension_returns_json_error(self):
        archive = zip_of({"a.jpg": jpeg()})
        response, thumbnails, load = self.upload_ajax(
            "photos.txt", archive, "text/plain"
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("zip", data["message"].lower())
        thumbnails.assert_not_called()
        load.assert_not_called()

    def test_ajax_file_too_large_returns_json_error(self):
        archive = zip_of({"a.jpg": jpeg()})
        with mock.patch("gestion.views.MAX_UPLOAD_SIZE", 10):
            response, thumbnails, load = self.upload_ajax("big.zip", archive)

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("taille maximale", data["message"])
        thumbnails.assert_not_called()
        load.assert_not_called()

    def test_ajax_success_returns_json_success(self):
        archive = zip_of({"a.jpg": jpeg(), "b.jpg": jpeg()})
        response, thumbnails, load = self.upload_ajax("photos.zip", archive)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertEqual(data["status"], "success")
        thumbnails.assert_called_once_with("sobriete")
        load.assert_called_once_with("sobriete")

    def test_ajax_unknown_gallery_returns_json_404(self):
        response = self.client.post(
            "/gestion/gallery/nope",
            {"zipfile": SimpleUploadedFile("a.zip", zip_of({"a.jpg": jpeg()}))},
            **self.ajax_headers,
        )

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("galerie", data["message"].lower())

    def test_non_ajax_not_a_zip_still_returns_400_html(self):
        """Le fallback non-AJAX continue de fonctionner (rétrocompatibilité)."""
        response, thumbnails, load = self.upload("photos.zip", b"not a zip")

        self.assertEqual(response.status_code, 400)
        self.assertIn("zip", response.content.decode().lower())
        thumbnails.assert_not_called()
        load.assert_not_called()

    def test_ajax_unexpected_error_returns_json_500(self):
        """Une erreur inattendue garde le contrat JSON pour une requête AJAX."""
        archive = zip_of({"a.jpg": jpeg()})
        # Answering in JSON hides the exception from Django: it has to be
        # logged here, or nothing tells why an import failed.
        with mock.patch(
            "gestion.views.load_zip_into_gallery", side_effect=OSError("disk full")
        ), self.assertLogs("gestion.views", level="ERROR") as logs:
            response, thumbnails, load = self.upload_ajax("photos.zip", archive)

        self.assertIn("disk full", logs.output[0])
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("erreur", data["message"].lower())
        thumbnails.assert_not_called()
        load.assert_not_called()
        self.assertEqual(self.zips_left(), [])

    def test_non_ajax_unexpected_error_still_raises(self):
        """Le fallback non-AJAX laisse l'exception remonter (500 Django)."""
        archive = zip_of({"a.jpg": jpeg()})
        with mock.patch(
            "gestion.views.load_zip_into_gallery", side_effect=OSError("disk full")
        ):
            with self.assertRaises(OSError):
                self.upload("photos.zip", archive)
        self.assertEqual(self.zips_left(), [])
