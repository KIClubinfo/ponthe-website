import io
import json
import os
import re

from api.models import TEAM_FOLDER, Team, TeamRole
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image


def picture(size=(3000, 2000), mode="RGB", fmt="JPEG", name="groupe.jpg"):
    """An upload as it comes out of a camera or a design tool."""
    buffer = io.BytesIO()
    Image.new(mode, size, (200, 80, 40) if mode == "RGB" else (200, 80, 40, 0)).save(
        buffer, fmt
    )
    return SimpleUploadedFile(name, buffer.getvalue(), f"image/{fmt.lower()}")


def forget_uploads():
    """
    Take the pictures uploaded by a test off the media folder.

    The database is rolled back after each test, the files are not: left in
    place, the next upload for the same promotion would get another name.
    """
    folder = os.path.join(settings.MEDIA_ROOT, TEAM_FOLDER)
    for name in os.listdir(folder):
        if name != "028.jpg":
            os.remove(os.path.join(folder, name))


def team_of_page(client):
    """The team the home page is handed, as the page's own code reads it."""
    page = client.get("/").content.decode()
    data = re.search(
        r'<script id="team-data" type="application/json">(.*?)</script>', page, re.S
    )
    return json.loads(data.group(1))


def inline_rows(rows, initial=0):
    """The fields of the roles table of the admin form."""
    data = {
        "roles-TOTAL_FORMS": str(len(rows)),
        "roles-INITIAL_FORMS": str(initial),
        "roles-MIN_NUM_FORMS": "0",
        "roles-MAX_NUM_FORMS": "1000",
    }
    for index, row in enumerate(rows):
        for field, value in row.items():
            data[f"roles-{index}-{field}"] = value
    return data


class CurrentTeamTest(TestCase):
    """The team the home page used to spell out is now a row like any other."""

    def test_the_team_written_in_the_code_was_carried_over(self):
        team = Team.objects.get()
        self.assertEqual((team.name, team.current), ("028", True))
        self.assertEqual(team.roles.count(), 9)
        self.assertTrue(
            os.path.isfile(os.path.join(settings.MEDIA_ROOT, TEAM_FOLDER, "028.jpg"))
        )

    def test_the_home_page_is_handed_the_team(self):
        team = team_of_page(self.client)
        self.assertEqual(team["name"], "028")
        self.assertEqual(team["photo"], "/media/.equipe/028.jpg")
        self.assertEqual(
            [section["title"] for section in team["sections"]],
            ["Le Bureau", "Responsables", "Pôle Création"],
        )
        bureau, _, creation = team["sections"]
        self.assertEqual(
            bureau["roles"][0], {"title": "Présidente", "people": ["Alice Dubreux"]}
        )
        self.assertEqual(
            [(role["title"], len(role["people"])) for role in creation["roles"]],
            [("Vidéastes", 4), ("Photographes", 8)],
        )

    def test_the_picture_is_served_to_everyone(self):
        response = self.client.get("/media/.equipe/028.jpg")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Accel-Redirect"], "/protected/.equipe/028.jpg")
        # Its neighbours in the media folder are not.
        self.assertEqual(self.client.get("/media/.corbeille/x.jpg").status_code, 403)

    def test_no_team_on_display(self):
        Team.objects.update(current=False)
        self.assertIsNone(team_of_page(self.client))
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_what_is_typed_in_cannot_break_out_of_the_page(self):
        team = Team.objects.get()
        team.roles.all().delete()
        TeamRole.objects.create(
            team=team,
            section="</script><script>alert(1)</script>",
            title="<b>Trez</b>",
            people="Ada & Co",
        )
        page = self.client.get("/").content.decode()
        self.assertNotIn("<script>alert(1)", page)
        self.assertEqual(
            team_of_page(self.client)["sections"][0]["roles"][0],
            {"title": "<b>Trez</b>", "people": ["Ada & Co"]},
        )


class TeamModelTest(TestCase):
    def setUp(self):
        self.addCleanup(forget_uploads)

    def test_only_one_team_is_on_display(self):
        old = Team.objects.get()
        new = Team.objects.create(name="029", current=True)
        old.refresh_from_db()
        self.assertFalse(old.current)
        self.assertEqual(team_of_page(self.client)["name"], "029")

        # Putting the old one back takes the new one off.
        old.current = True
        old.save()
        new.refresh_from_db()
        self.assertFalse(new.current)

    def test_a_team_kept_in_reserve_changes_nothing(self):
        Team.objects.create(name="029")
        self.assertEqual(team_of_page(self.client)["name"], "028")

    def test_roles_are_grouped_by_section_in_the_order_given(self):
        team = Team.objects.create(name="029", current=True)
        rows = [
            ("Bureau", "Prez", " Ada Lovelace ", 2),
            ("Création", "Photographes", "Nadar,, Vivian Maier ,", 3),
            ("Bureau", "Trez", "Alan Turing", 1),
            ("Création", "Vidéastes", "", 4),
        ]
        for section, title, people, order in rows:
            TeamRole.objects.create(
                team=team, section=section, title=title, people=people, order=order
            )
        self.assertEqual(
            team_of_page(self.client)["sections"],
            [
                {
                    "title": "Bureau",
                    "roles": [
                        {"title": "Trez", "people": ["Alan Turing"]},
                        {"title": "Prez", "people": ["Ada Lovelace"]},
                    ],
                },
                {
                    "title": "Création",
                    "roles": [
                        {"title": "Photographes", "people": ["Nadar", "Vivian Maier"]},
                        {"title": "Vidéastes", "people": []},
                    ],
                },
            ],
        )

    def test_a_line_added_without_a_number_goes_last(self):
        # Nobody should have to renumber the table to add one name.
        team = Team.objects.get()
        added = TeamRole.objects.create(
            team=team, section="Responsables", title="Respo Web", people="Ada Lovelace"
        )
        self.assertEqual(added.order, 9)
        self.assertEqual(team.roles.last(), added)
        responsables = team_of_page(self.client)["sections"][1]
        self.assertEqual(responsables["roles"][-1]["title"], "Respo Web")

        # A number that was typed in is kept, and so is the one of a line
        # that is only being corrected.
        first = TeamRole.objects.create(
            team=team, section="Le Bureau", title="Prez d'honneur", people="X", order=3
        )
        self.assertEqual(first.order, 3)
        president = team.roles.get(title="Présidente")
        president.people = "Grace Hopper"
        president.save()
        self.assertEqual(president.order, 0)

    def stored(self, team):
        with Image.open(team.photo.path) as image:
            image.load()
            return image

    def test_an_uploaded_picture_is_made_fit_for_the_page(self):
        team = Team.objects.create(name="029", photo=picture(size=(6000, 4000)))
        self.assertEqual(team.photo.name, ".equipe/029.jpg")
        image = self.stored(team)
        self.assertEqual(
            (image.format, image.mode, image.size), ("JPEG", "RGB", (2400, 1600))
        )
        self.assertLess(os.path.getsize(team.photo.path), 1024 * 1024)

    def test_a_small_picture_is_not_blown_up(self):
        team = Team.objects.create(name="029", photo=picture(size=(1200, 800)))
        self.assertEqual(self.stored(team).size, (1200, 800))

    def test_a_png_with_transparency_becomes_a_jpeg_on_white(self):
        upload = picture(size=(800, 600), mode="RGBA", fmt="PNG", name="groupe.png")
        team = Team.objects.create(name="Promo 029 !", photo=upload)
        self.assertEqual(team.photo.name, ".equipe/promo-029.jpg")
        image = self.stored(team)
        self.assertEqual((image.format, image.mode), ("JPEG", "RGB"))
        self.assertGreater(min(image.getpixel((10, 10))), 240)

    def test_a_new_picture_gets_a_new_address(self):
        # Same address, and browsers would keep showing last year's faces.
        team = Team.objects.create(name="029", photo=picture())
        first = team.photo.name
        team.photo = picture(size=(900, 600))
        team.save()
        self.assertNotEqual(team.photo.name, first)
        self.assertTrue(team.photo.name.startswith(".equipe/029"))

    def test_saving_again_leaves_the_picture_alone(self):
        team = Team.objects.create(name="029", photo=picture())
        name, modified = team.photo.name, os.path.getmtime(team.photo.path)
        team.current = True
        team.save()
        self.assertEqual(team.photo.name, name)
        self.assertEqual(os.path.getmtime(team.photo.path), modified)


class TeamAdminTest(TestCase):
    """The handover, as done in the admin by someone who runs the galleries."""

    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user("student")
        # Staff without any admin permission: what a new board member gets.
        cls.manager = User.objects.create_user("manager", is_staff=True)
        cls.admin = User.objects.create_superuser("admin")

    def setUp(self):
        self.addCleanup(forget_uploads)

    def test_managers_reach_the_teams_and_nothing_else(self):
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get("/admin/api/team/").status_code, 200)
        self.assertEqual(self.client.get("/admin/api/team/add/").status_code, 200)
        self.assertEqual(self.client.get("/admin/auth/user/").status_code, 403)
        self.assertEqual(self.client.get("/admin/api/gallery/").status_code, 403)

    def test_other_accounts_do_not(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get("/admin/api/team/").status_code, 302)

    def test_the_form_is_in_french_and_says_how_to_hand_over(self):
        self.client.force_login(self.manager)
        team = Team.objects.get()
        page = self.client.get(f"/admin/api/team/{team.pk}/change/").content.decode()
        self.assertIn("Passation.", page)
        self.assertIn("Années scolaires", page)
        self.assertIn("Enregistrer en tant que nouveau", page)
        self.assertIn("photo de groupe", page.lower())

    def test_adding_a_team_puts_it_on_the_home_page(self):
        self.client.force_login(self.manager)
        rows = [
            {
                "section": "Le Bureau",
                "title": "Présidente",
                "people": "Ada Lovelace",
                "order": "0",
            },
            {
                "section": "Pôle Création",
                "title": "Photographes",
                "people": "Nadar, Vivian Maier",
                "order": "1",
            },
        ]
        data = {
            "name": "029",
            "current": "on",
            "photo": picture(),
            "_save": "Enregistrer",
        }
        response = self.client.post(
            "/admin/api/team/add/", {**data, **inline_rows(rows)}
        )
        self.assertEqual(response.status_code, 302, response.content.decode()[:2000])

        team = team_of_page(self.client)
        self.assertEqual(
            (team["name"], team["photo"]), ("029", "/media/.equipe/029.jpg")
        )
        self.assertEqual(
            team["sections"][1],
            {
                "title": "Pôle Création",
                "roles": [
                    {"title": "Photographes", "people": ["Nadar", "Vivian Maier"]}
                ],
            },
        )
        self.assertFalse(Team.objects.get(name="028").current)

    def test_a_team_put_on_display_without_a_picture_is_pointed_out(self):
        self.client.force_login(self.manager)
        data = {
            "name": "029",
            "current": "on",
            "_save": "Enregistrer",
            **inline_rows([]),
        }
        response = self.client.post("/admin/api/team/add/", data, follow=True)
        self.assertContains(response, "sans photo de groupe")
        self.assertIsNone(team_of_page(self.client)["photo"])

        # Kept in reserve, nothing is shown yet: nothing to point out.
        data = {"name": "030", "_save": "Enregistrer", **inline_rows([])}
        response = self.client.post("/admin/api/team/add/", data, follow=True)
        self.assertNotContains(response, "sans photo de groupe")

    def test_a_file_that_is_not_a_picture_is_refused(self):
        self.client.force_login(self.manager)
        upload = SimpleUploadedFile("groupe.jpg", b"not a picture", "image/jpeg")
        data = {
            "name": "029",
            "photo": upload,
            "_save": "Enregistrer",
            **inline_rows([]),
        }
        response = self.client.post("/admin/api/team/add/", data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Team.objects.filter(name="029").exists())

    def test_last_years_team_is_the_starting_point_of_the_next(self):
        self.client.force_login(self.manager)
        old = Team.objects.get()
        rows = [
            {
                "id": str(role.pk),
                "team": str(old.pk),
                "section": role.section,
                "title": role.title,
                # The same roles, held by other people.
                "people": "Ada Lovelace" if role.title == "Présidente" else role.people,
                "order": str(role.order),
            }
            for role in old.roles.all()
        ]
        data = {"name": "029", "current": "on", "photo": picture(), "_saveasnew": "1"}
        response = self.client.post(
            f"/admin/api/team/{old.pk}/change/",
            {**data, **inline_rows(rows, initial=9)},
        )
        self.assertEqual(response.status_code, 302, response.content.decode()[:2000])

        new = Team.objects.get(name="029")
        self.assertEqual(new.roles.count(), 9)
        self.assertEqual(new.roles.get(title="Présidente").people, "Ada Lovelace")
        # Last year's team is kept as it was, off the home page.
        old.refresh_from_db()
        self.assertFalse(old.current)
        self.assertEqual(old.roles.get(title="Présidente").people, "Alice Dubreux")
        self.assertEqual(team_of_page(self.client)["name"], "029")


class AccountActionsTest(TestCase):
    """Giving and taking back the keys, a handover's other half."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser("admin")
        cls.newcomers = [User.objects.create_user(f"new{i}") for i in range(3)]
        cls.leaving = User.objects.create_user("leaving", is_staff=True)
        cls.leaving_admin = User.objects.create_superuser("leaving-admin")

    def act(self, action, users):
        return self.client.post(
            "/admin/auth/user/",
            {"action": action, "_selected_action": [str(user.pk) for user in users]},
            follow=True,
        )

    def test_several_accounts_are_given_access_at_once(self):
        self.client.force_login(self.admin)
        response = self.act("grant_management", self.newcomers[:2])
        self.assertContains(response, "2 compte(s) ont maintenant accès")
        self.assertEqual(
            list(User.objects.filter(username__startswith="new", is_staff=True)),
            self.newcomers[:2],
        )
        # Running the galleries, not the whole administration.
        self.assertFalse(
            User.objects.filter(username__startswith="new", is_superuser=True)
        )

    def test_access_is_taken_back_but_never_from_oneself(self):
        self.client.force_login(self.admin)
        response = self.act(
            "revoke_management", [self.leaving, self.leaving_admin, self.admin]
        )
        self.assertContains(response, "2 compte(s) n&#x27;ont plus aucun accès")
        self.assertContains(response, "Votre propre compte n&#x27;a pas été modifié")
        for user in (self.leaving, self.leaving_admin):
            user.refresh_from_db()
            self.assertEqual((user.is_staff, user.is_superuser), (False, False))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_staff and self.admin.is_superuser)

    def test_only_those_who_manage_accounts_can_use_them(self):
        self.client.force_login(self.leaving)
        self.assertEqual(self.act("grant_management", self.newcomers).status_code, 403)
        self.assertFalse(User.objects.filter(username__startswith="new", is_staff=True))


class RetiredPagesTest(TestCase):
    def test_pages_that_led_nowhere_are_gone(self):
        for url in (
            "/material/",
            "/password_reset/",
            "/password_reset/done/",
            "/password_change/",
            "/reset/done/",
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_logging_out_still_works(self):
        self.client.force_login(User.objects.create_user("student"))
        response = self.client.get("/logout/")
        self.assertRedirects(response, "/", fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)
