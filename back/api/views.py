import os
import tempfile
import zipfile

import galerie.loader as loader
import galerie.settings as settings
from api.models import File, Gallery, Report, Year
from api.permissions import IsManager, is_manager
from api.serializers import (
    FileSerializer,
    GallerySerializer,
    PromoSerializer,
    ReportSerializer,
    YearSerializer,
)
from django.conf import settings as django_settings
from django.db import IntegrityError
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
def getRoutes(request):
    routes = [
        {
            "Endpoint": "/api/galleries",
            "method": "GET",
            "description": "Return all galleries that a user can see",
        },
        {
            "Endpoint": "/api/galleries/create",
            "method": "POST",
            "description": "Create a new gallery",
            "Format of the request:": {
                "name": "name of the gallery",
                "description": "gallery's description",
                "date": "creation date",
                "visibility": "gallery's visibility",
                "type": "photo or video?",
                "year": "creation date's year",
            },
        },
        {
            "Endpoint": "/api/gallery/pics",
            "method": "GET",
            "description": "Return all pics from a gallery",
            "Format of the request:": {
                "id": "gallery_id",
            },
        },
        {
            "Endpoint": "/api/year/create",
            "method": "POST",
            "description": "Create a new year",
            "Format of the request:": {
                "name": "name of the year (eg. 2022-2023)",
            },
        },
        {
            "Endpoint": "/api/promo/create",
            "method": "POST",
            "description": "Create a new promotion",
            "Format of the request:": {
                "name": "name of the promo (eg. 026)",
                "year": "year object corresponding to first year of this promo",
            },
        },
    ]

    return Response(routes)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_view(request):
    if request.method == "GET":
        galleries = Gallery.objects.all()
        if not request.user.is_authenticated:
            galleries = galleries.filter(visibility=Gallery.Visibility.PUBLIC)

        if request.GET.get("view") is not None:
            galleries = galleries.filter(view=request.GET.get("view"))

        if request.user.is_authenticated and not is_manager(request.user):
            galleries = galleries.filter(
                Q(visibility=Gallery.Visibility.PUBLIC)
                | Q(visibility=Gallery.Visibility.SCHOOL)
            )

        galleries = galleries.order_by("-date")
        serializer = GallerySerializer(galleries, many=True)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_galleries(request):
    if not request.user.is_authenticated:
        galleries = Gallery.objects.filter(
            visibility=Gallery.Visibility.PUBLIC
        ).order_by("-date")
    elif is_manager(request.user):
        galleries = Gallery.objects.filter(view=Gallery.View.GALLERY).order_by("-date")
    else:
        galleries = Gallery.objects.filter(
            Q(visibility=Gallery.Visibility.SCHOOL)
            | Q(visibility=Gallery.Visibility.PUBLIC) & Q(view=Gallery.View.GALLERY)
        ).order_by("-date")
    serializer = GallerySerializer(galleries, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_expositions(request):
    if not request.user.is_authenticated:
        galleries = Gallery.objects.filter(
            visibility=Gallery.Visibility.PUBLIC
        ).order_by("-date")
    elif is_manager(request.user):
        galleries = Gallery.objects.filter(view=Gallery.View.EXPOSITION).order_by(
            "-date"
        )
    else:
        galleries = Gallery.objects.filter(
            Q(visibility=Gallery.Visibility.SCHOOL)
            | Q(visibility=Gallery.Visibility.PUBLIC) & Q(view=Gallery.View.EXPOSITION)
        ).order_by("-date")
    serializer = GallerySerializer(galleries, many=True)
    return Response(serializer.data)


FORBIDDEN_GALLERY = {
    "status": "error",
    "message": "Vous n'êtes pas autorisé à voir cette galerie.",
}


@api_view(["POST"])
@permission_classes([AllowAny])
def get_gallery(request):
    gallery = Gallery.objects.filter(slug=request.data.get("slug")).first()
    if gallery is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if not gallery.can_user_access(request.user):
        return Response(FORBIDDEN_GALLERY, status=403)
    return Response(GallerySerializer(gallery).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def get_pics(request):
    gallery = Gallery.objects.filter(slug=request.data.get("slug")).first()
    if gallery is None:
        return Response(
            {"status": "error", "message": "Cette galerie n'existe pas."}, status=404
        )
    if not gallery.can_user_access(request.user):
        return Response(FORBIDDEN_GALLERY, status=403)
    files = File.objects.filter(gallery=gallery)
    return Response(data=FileSerializer(files, many=True).data)


@api_view(["POST"])
@permission_classes([IsManager])
def create_gallery(request):
    if "year" not in request.data:
        request.data["year"] = Year.objects.last().pk
    request.data["slug"] = slugify(request.data["name"])
    if request.data["name"] == "":
        return Response(
            {
                "status": "error",
                "message": "Le nom de la galerie ne peut pas être vide.",
            },
            status=400,
        )
    if Gallery.objects.filter(slug=request.data["slug"]).exists():
        return Response(
            {"status": "error", "message": "Une galerie avec ce nom existe déjà."},
            status=400,
        )
    serializer = GallerySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    # Folders first: if they cannot be made, no gallery is left without one.
    try:
        for folder in ("uploads", "thumbnails"):
            os.makedirs(loader.gallery_path(request.data["slug"], folder))
    except OSError:
        return Response(
            {
                "status": "error",
                "message": "Impossible de créer les dossiers de la galerie.",
            },
            status=400,
        )
    serializer.save()

    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsManager])
def create_year(request):
    serializer = YearSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsManager])
def create_promo(request):
    serializer = PromoSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


# The two routes below re-run the import of a gallery, e.g. after the worker was
# down. They take the gallery slug, never a path: the folder is derived from it.
@api_view(["POST"])
@permission_classes([IsManager])
def load_folder_into_gallery(request):
    gal = get_object_or_404(Gallery, slug=request.data.get("slug"))
    loader.load_folder_into_gallery.delay(gal.slug)
    return Response(GallerySerializer(gal).data)


@api_view(["POST"])
@permission_classes([IsManager])
def generate_thumbnails(request):
    gal = get_object_or_404(Gallery, slug=request.data.get("slug"))
    loader.generate_thumbnails.delay(gal.slug)
    return Response(status=200)


@api_view(["POST"])
@permission_classes([IsManager])
def change_visibility(request):
    gallery = Gallery.objects.filter(slug=request.data.get("slug")).first()
    if gallery is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    # save() does not check `choices`: an unknown value would be stored as is.
    if request.data.get("visibility") not in Gallery.Visibility.values:
        return Response(
            {"status": "error", "message": "Visibilité inconnue."}, status=400
        )
    gallery.visibility = request.data["visibility"]
    gallery.save()
    return Response(GallerySerializer(gallery).data)


@api_view(["POST"])
@permission_classes([IsManager])
def change_view(request):
    gallery = Gallery.objects.filter(slug=request.data.get("slug")).first()
    if gallery is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.data.get("view") not in Gallery.View.values:
        return Response({"status": "error", "message": "Vue inconnue."}, status=400)
    gallery.view = request.data["view"]
    gallery.save()
    return Response(GallerySerializer(gallery).data)


@api_view(["POST"])
@permission_classes([IsManager])
def delete_gallery(request):
    gal = Gallery.objects.get(name=request.data["name"])
    # api.signals takes the folder off the disk.
    gal.delete()
    return Response(GallerySerializer(gal).data)


@api_view(["POST"])
@permission_classes([IsManager])
def delete_pic(request):
    gallery = Gallery.objects.get(name=request.data["name"])
    file = File.objects.get(
        gallery=gallery, file_full_name=request.data["file_full_name"]
    )
    # api.signals takes the files off the disk.
    file.delete()
    return Response(FileSerializer(file).data)


def selection_error(message, status=400):
    return Response({"status": "error", "message": message}, status=status)


@api_view(["POST"])
@permission_classes([AllowAny])
def download_pics(request):
    """
    Zip the selected pictures of a gallery, for anyone who can see them.

    Anyone includes a visitor who is not logged in, on a public gallery: the
    selection is capped in number and in weight, and the archive is written to
    a temporary file and sent from there, so that no request can hold hundreds
    of megabytes in the memory of a worker. Pictures are stored, not deflated:
    a JPEG does not get any smaller.
    """
    gallery = Gallery.objects.filter(slug=request.data.get("slug")).first()
    if gallery is None:
        return selection_error("Cette galerie n'existe pas.", 404)
    if not gallery.can_user_access(request.user):
        return Response(FORBIDDEN_GALLERY, status=403)
    names = request.data.get("file_full_names")
    if not isinstance(names, list) or len(names) == 0:
        return selection_error("Aucune photo sélectionnée.")
    if not all(isinstance(name, str) for name in names):
        return selection_error("Sélection invalide.")
    if len(names) > django_settings.DOWNLOAD_MAX_PHOTOS:
        return selection_error(
            f"Sélection trop grande : {django_settings.DOWNLOAD_MAX_PHOTOS} photos "
            "au maximum par téléchargement."
        )

    members = []
    total = 0
    for file in File.objects.filter(gallery=gallery, file_full_name__in=names):
        # Rows are written from a folder listing, but the admin lets a name be
        # typed in: one holding a path must not reach outside the gallery.
        if os.path.basename(file.file_full_name) != file.file_full_name:
            continue
        path = loader.gallery_path(gallery.slug, "uploads", file.file_full_name)
        if os.path.isfile(path):
            members.append((file.file_full_name, path))
            total += os.path.getsize(path)
    if not members:
        return selection_error("Aucune de ces photos n'existe.", 404)
    if total > django_settings.DOWNLOAD_MAX_BYTES:
        megabytes = django_settings.DOWNLOAD_MAX_BYTES // (1024 * 1024)
        return selection_error(
            f"Sélection trop lourde : {megabytes} Mo au maximum par téléchargement."
        )

    archive_file = tempfile.TemporaryFile()
    with zipfile.ZipFile(archive_file, "w", zipfile.ZIP_STORED) as archive:
        for name, path in members:
            archive.write(path, arcname=name)
    archive_file.seek(0)
    # FileResponse reads the file piece by piece and closes it when done.
    return FileResponse(
        archive_file,
        as_attachment=True,
        filename=f"{gallery.slug}-selection.zip",
        content_type="application/zip",
    )


@api_view(["POST"])
@permission_classes([IsManager])
def delete_pics(request):
    """
    Bulk version of delete_pic: the manager selected several at once.

    The files go with the rows (see api.signals), so that a picture deleted
    here is neither served any more nor brought back by the next import.
    """
    gallery = Gallery.objects.filter(slug=request.data.get("slug")).first()
    if gallery is None:
        return Response(
            {"status": "error", "message": "Cette galerie n'existe pas."}, status=404
        )
    names = request.data.get("file_full_names")
    if not isinstance(names, list) or len(names) == 0:
        return Response(
            {"status": "error", "message": "Aucune photo sélectionnée."}, status=400
        )
    files = File.objects.filter(gallery=gallery, file_full_name__in=names)
    deleted = files.count()
    files.delete()
    return Response({"status": "ok", "deleted": deleted})


@api_view(["GET"])
@permission_classes([AllowAny])
def years(request):
    years = Year.objects.all().order_by("pk").reverse()
    serializer = YearSerializer(years, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([AllowAny])
def report_pic(request):
    """A logged-in user who can see the gallery flags one of its pictures."""
    gallery = Gallery.objects.filter(slug=request.data.get("slug")).first()
    if gallery is None:
        return Response(
            {"status": "error", "message": "Cette galerie n'existe pas."}, status=404
        )
    if not request.user.is_authenticated:
        return Response(
            {
                "status": "error",
                "message": "Connectez-vous pour signaler une photo.",
            },
            status=403,
        )
    if not gallery.can_user_access(request.user):
        return Response(FORBIDDEN_GALLERY, status=403)
    if request.data.get("category") not in Report.Category.values:
        return Response(
            {"status": "error", "message": "Motif de signalement inconnu."}, status=400
        )
    file = File.objects.filter(
        gallery=gallery, file_full_name=request.data.get("file_full_name")
    ).first()
    if file is None:
        return Response(
            {"status": "error", "message": "Cette photo n'existe pas."}, status=404
        )
    if Report.objects.filter(file=file, reporter=request.user).exists():
        return Response(
            {
                "status": "error",
                "message": "Vous avez déjà signalé cette photo.",
            },
            status=400,
        )
    message = request.data.get("message", "")
    if not isinstance(message, str) or len(message) > 1000:
        return Response({"status": "error", "message": "Message invalide."}, status=400)
    try:
        report = Report.objects.create(
            file=file,
            reporter=request.user,
            category=request.data["category"],
            message=message,
        )
    except IntegrityError:
        # A concurrent request of the same user slipped past the check above.
        return Response(
            {
                "status": "error",
                "message": "Vous avez déjà signalé cette photo.",
            },
            status=400,
        )
    return Response(ReportSerializer(report).data, status=201)


@api_view(["POST"])
@permission_classes([IsManager])
def gallery_reports(request):
    """For the management side: who flagged which picture, and why."""
    gallery = Gallery.objects.filter(slug=request.data.get("slug")).first()
    if gallery is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    reports = (
        Report.objects.filter(file__gallery=gallery)
        .select_related("file", "reporter")
        .order_by("-created_at", "-pk")
    )
    return Response(ReportSerializer(reports, many=True).data)


@api_view(["POST"])
@permission_classes([IsManager])
def dismiss_report(request):
    """A manager has dealt with a report, or found it groundless."""
    report_id = request.data.get("id")
    if not isinstance(report_id, int) or isinstance(report_id, bool):
        return Response(
            {"status": "error", "message": "Signalement inconnu."}, status=400
        )
    deleted, _ = Report.objects.filter(pk=report_id).delete()
    if not deleted:
        return Response(
            {"status": "error", "message": "Signalement inconnu."}, status=404
        )
    return Response({"status": "ok"})
