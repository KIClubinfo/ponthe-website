from api.views import getRoutes
from django.test import SimpleTestCase, TestCase
from django.urls import resolve, reverse
from galerie.views import LoginView, galleries, gallery, index
from gestion.views import index_view


class TestUrls(SimpleTestCase):
    def test_login_url_resolves(self):
        url = reverse("login")
        self.assertEqual(resolve(url).func.view_class, LoginView)

    def test_index_url_resolves(self):
        url = reverse("index")
        self.assertEqual(resolve(url).func, index)

    def test_gallery_url_resolves(self):
        url = reverse("gallery", args=["slug"])
        self.assertEqual(resolve(url).func, gallery)

    def test_galleries_url_resolves(self):
        url = reverse("galleries")
        self.assertEqual(resolve(url).func, galleries)

    def test_gestion_url_resolves(self):
        url = reverse("gestion")
        self.assertEqual(resolve(url).func, index_view)

    def test_api_url_resolves(self):
        url = reverse("api-routes")
        self.assertEqual(resolve(url).func, getRoutes)


class TestPages(TestCase):
    def test_pages_are_complete_documents(self):
        for url in ("/", "/galleries/", "/gallery/gala", "/login/"):
            with self.subTest(url=url):
                page = self.client.get(url).content.decode()
                self.assertTrue(page.lstrip().startswith("<!DOCTYPE html>"))
                self.assertEqual(page.count("<head>"), 1)
                self.assertIn('<meta name="viewport"', page)

    def test_bundle_url_changes_with_each_build(self):
        page = self.client.get("/gallery/gala").content.decode()
        self.assertRegex(page, r'src="/static/react/gallery\.bundle\.js\?v=\d+"')
