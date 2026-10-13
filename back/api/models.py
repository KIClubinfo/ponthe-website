import io

from api.permissions import is_manager
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from PIL import Image, ImageOps


class Year(models.Model):
    name = models.CharField(
        "année scolaire",
        primary_key=True,
        max_length=10,
        help_text="Sous la forme 2027-2028. Une galerie que l'on crée est "
        "rangée dans l'année la plus récente.",
    )

    class Meta:
        verbose_name = "année scolaire"
        verbose_name_plural = "années scolaires"

    def __str__(self):
        return self.name


class Promo(models.Model):
    name = models.CharField(primary_key=True, max_length=10)
    first_year = models.ForeignKey(Year, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "promotion"
        verbose_name_plural = "promotions"


# TODO: Create a year model ?
class Gallery(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(blank=False, max_length=1000, unique=True)
    # Every lookup goes through the slug, and it names the folder on disk.
    slug = models.SlugField(max_length=1000, blank=False, default="", unique=True)
    description = models.CharField(max_length=10000)
    date = models.DateTimeField(blank=False, default=timezone.now)

    class Visibility(models.TextChoices):
        PUBLIC = "publique"
        SCHOOL = "école"
        PRIVATE = "privée"

    visibility = models.CharField(
        choices=Visibility.choices, default=Visibility.PRIVATE, max_length=10
    )

    class Type(models.TextChoices):
        PHOTO = "photo"
        VIDEO = "video"

    type = models.CharField(
        blank=False, default=Type.PHOTO, choices=Type.choices, max_length=10
    )
    year = models.ForeignKey(Year, on_delete=models.PROTECT, default=None)

    class View(models.TextChoices):
        GALLERY = "galerie"
        EXPOSITION = "exposition"

    view = models.CharField(
        blank=False, default=View.GALLERY, choices=View.choices, max_length=20
    )

    class Meta:
        verbose_name = "galerie"
        verbose_name_plural = "galeries"

    def can_user_access(self, user):
        """
        The single access rule for a gallery, its picture list and its files:
        public galleries are open to everyone, school galleries to any logged-in
        user, and everything else (private) to those who run the galleries.
        """
        if self.visibility == Gallery.Visibility.PUBLIC:
            return True
        if not user.is_authenticated:
            return False
        if self.visibility == Gallery.Visibility.SCHOOL:
            return True
        return is_manager(user)


class File(models.Model):
    id = models.AutoField(primary_key=True)
    file_name = models.CharField(blank=False, max_length=1000)
    file_extension = models.CharField(blank=False, max_length=100)
    file_full_name = models.CharField(blank=False, max_length=1100)
    link = models.CharField(max_length=10000)
    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE, default=None)

    class Meta:
        verbose_name = "photo"
        verbose_name_plural = "photos"
        constraints = [
            # Two import tasks running at once used to register each picture twice.
            models.UniqueConstraint(
                fields=["gallery", "file_full_name"], name="unique_file_per_gallery"
            )
        ]


# Folder of the team pictures inside the media folder, served to everyone.
# The dot keeps it apart from the galleries, whose folders are named after a
# slug: no slug starts with one.
TEAM_FOLDER = ".equipe"
TEAM_PHOTO_MAX_SIDE = 2400


def team_photo_path(team, filename):
    return f"{TEAM_FOLDER}/{slugify(team.name) or 'equipe'}.jpg"


def as_web_photo(upload):
    """
    A picture as it comes out of a camera, made fit for a web page.

    The home page shows it full width: twenty megabytes straight from the
    camera would be downloaded by every visitor. Turned the right way up,
    brought down to a screen's worth of pixels, and saved as a JPEG whatever
    it came as.
    """
    with Image.open(upload) as image:
        image = ImageOps.exif_transpose(image)
        if image.mode != "RGB":
            # Transparent areas would turn black in a JPEG.
            layer = image.convert("RGBA")
            image = Image.new("RGB", layer.size, "white")
            image.paste(layer, mask=layer.getchannel("A"))
        image.thumbnail((TEAM_PHOTO_MAX_SIDE, TEAM_PHOTO_MAX_SIDE))
        buffer = io.BytesIO()
        image.save(buffer, "JPEG", quality=85, optimize=True, progressive=True)
    return ContentFile(buffer.getvalue())


class Team(models.Model):
    """
    The people who run the club for a year, as the home page shows them.

    Nothing in the code names a promotion: handing over to the next one is
    adding a team in the admin and ticking "affichée sur le site".
    """

    name = models.CharField(
        "promotion",
        max_length=20,
        unique=True,
        help_text="Le numéro de la promotion, par exemple 029.",
    )
    photo = models.ImageField(
        "photo de groupe",
        upload_to=team_photo_path,
        blank=True,
        help_text="De préférence en largeur. Elle est redimensionnée à "
        "l'enregistrement : inutile de la réduire avant.",
    )
    current = models.BooleanField(
        "affichée sur le site",
        default=False,
        help_text="Une seule équipe est affichée : cocher celle-ci retire la "
        "précédente de la page d'accueil.",
    )
    created_at = models.DateTimeField("créée le", auto_now_add=True)

    class Meta:
        verbose_name = "équipe"
        verbose_name_plural = "équipes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Ponthé {self.name}"

    def save(self, *args, **kwargs):
        # A picture that was just uploaded, not one already in place.
        if self.photo and not self.photo._committed:
            self.photo.save("photo.jpg", as_web_photo(self.photo.file), save=False)
        super().save(*args, **kwargs)
        if self.current:
            Team.objects.exclude(pk=self.pk).filter(current=True).update(current=False)

    def on_display(self):
        """What the home page needs, or None while no team is on display."""
        sections = {}
        for role in self.roles.all():
            names = [name.strip() for name in role.people.split(",")]
            sections.setdefault(role.section, []).append(
                {"title": role.title, "people": [name for name in names if name]}
            )
        return {
            "name": self.name,
            "photo": self.photo.url if self.photo else None,
            "sections": [
                {"title": title, "roles": roles} for title, roles in sections.items()
            ],
        }


class TeamRole(models.Model):
    """One line of a team: a role and whoever holds it."""

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="roles")
    section = models.CharField(
        "rubrique",
        max_length=100,
        help_text="Le titre sous lequel la ligne est rangée : Le Bureau, "
        "Responsables, Pôle Création…",
    )
    title = models.CharField(
        "rôle", max_length=100, help_text="Présidente, Trez, Photographes…"
    )
    people = models.CharField(
        "nom(s)",
        max_length=2000,
        help_text="Un nom, ou plusieurs séparés par des virgules.",
    )
    order = models.PositiveSmallIntegerField(
        "ordre",
        default=0,
        help_text="Les lignes s'affichent par ordre croissant. Laisser 0 sur "
        "une nouvelle ligne la place à la fin.",
    )

    class Meta:
        verbose_name = "rôle"
        verbose_name_plural = "rôles"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.title} : {self.people}"

    def save(self, *args, **kwargs):
        # A line added without a number goes after the others, not before:
        # nobody should have to renumber a table to add one name.
        if self._state.adding and not self.order:
            last = self.team.roles.aggregate(last=models.Max("order"))["last"]
            self.order = 0 if last is None else last + 1
        super().save(*args, **kwargs)


class Report(models.Model):
    """Un signalement de photo par un utilisateur connecté."""

    id = models.AutoField(primary_key=True)
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Category(models.TextChoices):
        INAPPROPRIATE = "inapproprié"
        OFF_TOPIC = "hors sujet"
        QUALITY = "qualité"
        OTHER = "autre"

    category = models.CharField(
        blank=False, default=Category.OTHER, choices=Category.choices, max_length=20
    )
    message = models.CharField(blank=True, default="", max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "signalement"
        verbose_name_plural = "signalements"
        constraints = [
            # Signaler la même photo dix fois n'aide pas la modération.
            models.UniqueConstraint(
                fields=["file", "reporter"], name="one_report_per_user_per_file"
            )
        ]
