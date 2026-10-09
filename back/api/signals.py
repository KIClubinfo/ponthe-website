"""
Deleting a picture or a gallery also takes its files off the site.

Only the database row used to go. The files stayed where they were: still
served to whoever had the address, and registered again by the next import
into the gallery, which reads the whole folder.

Originals are not destroyed but moved to MEDIA_ROOT/.corbeille/<slug>/uploads/:
a selection is deleted in one click, and a photo club does not get its
originals back. Nothing serves that folder (".corbeille" cannot be the slug of
a gallery) and nothing empties it either: that is left to whoever runs the
server. Thumbnails are simply removed, they can be made again.
"""

import logging
import os
import shutil

from api.models import File, Gallery
from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)

TRASH = ".corbeille"


def gallery_folder(slug, *parts):
    return os.path.join(settings.MEDIA_ROOT, slug, *parts)


def trash_folder(slug):
    return os.path.join(settings.MEDIA_ROOT, TRASH, slug, "uploads")


def move_to_trash(path, slug):
    os.makedirs(trash_folder(slug), exist_ok=True)
    os.replace(path, os.path.join(trash_folder(slug), os.path.basename(path)))


@receiver(post_delete, sender=File)
def remove_picture_files(sender, instance, **kwargs):
    # `link` is "/media/<slug>": it still tells the folder when the gallery
    # itself is on its way out.
    slug = instance.link.rsplit("/", 1)[-1]
    name = instance.file_full_name
    if not slug or not name or os.path.basename(name) != name:
        return
    try:
        original = gallery_folder(slug, "uploads", name)
        if os.path.isfile(original):
            move_to_trash(original, slug)
        thumbnail = gallery_folder(slug, "thumbnails", name)
        if os.path.isfile(thumbnail):
            os.remove(thumbnail)
    except OSError:
        # The row is gone either way; a file left behind must not undo that.
        logger.exception("Could not take %s/%s off the disk", slug, name)


@receiver(post_delete, sender=Gallery)
def remove_gallery_folder(sender, instance, **kwargs):
    """What the pictures left behind: unregistered files and the folders."""
    slug = instance.slug
    if not slug or not os.path.isdir(gallery_folder(slug)):
        return
    try:
        uploads = gallery_folder(slug, "uploads")
        if os.path.isdir(uploads):
            for name in os.listdir(uploads):
                move_to_trash(os.path.join(uploads, name), slug)
        shutil.rmtree(gallery_folder(slug))
    except OSError:
        logger.exception("Could not remove the folder of gallery %s", slug)
