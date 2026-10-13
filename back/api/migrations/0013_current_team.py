import os
import shutil

from django.conf import settings
from django.db import migrations

# The team the home page used to spell out in its own code, moved to where
# the next one will be typed in. Runs once: a site that already has a team
# is left alone.
PROMOTION = "028"
PHOTO = os.path.join("galerie", "static", "assets", "img", "028_group.jpg")
ROLES = [
    ("Le Bureau", "Présidente", "Alice Dubreux"),
    ("Le Bureau", "V-Prez Photo", "Romain Soulabail"),
    ("Le Bureau", "V-Prez Vidéo", "Louis Cussoneau"),
    ("Le Bureau", "Trez", "Émilie Duccini"),
    ("Responsables", "Respo Matos", "Paul Lemeunier"),
    ("Responsables", "Respo Galeries", "Maxime Novo-Frelicot"),
    ("Responsables", "Respo Comm", "Vincent Huynh"),
    (
        "Pôle Création",
        "Vidéastes",
        "Océane Chia, Louis Laverrière, Clovis Vialard, Sophie Balmitgère",
    ),
    (
        "Pôle Création",
        "Photographes",
        "Maxime Préel, Pétronille Sylvestre, Juliette Houriez, Mathilde David, "
        "Sélène Baudoux, Saül Buchwald, Lucie Agnese, Maxence Brechon",
    ),
]


def copy_photo():
    """The picture shipped with the code, copied where uploads are kept."""
    name = ".equipe/028.jpg"
    target = os.path.join(settings.MEDIA_ROOT, name)
    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copyfile(os.path.join(settings.BASE_DIR, PHOTO), target)
    except OSError:
        # The team is shown without a picture until one is uploaded.
        return ""
    return name


def add_current_team(apps, schema_editor):
    Team = apps.get_model("api", "Team")
    TeamRole = apps.get_model("api", "TeamRole")
    if Team.objects.exists():
        return
    team = Team.objects.create(name=PROMOTION, photo=copy_photo(), current=True)
    TeamRole.objects.bulk_create(
        TeamRole(team=team, section=section, title=title, people=people, order=order)
        for order, (section, title, people) in enumerate(ROLES)
    )


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0012_team"),
    ]

    operations = [
        migrations.RunPython(add_current_team, migrations.RunPython.noop),
    ]
