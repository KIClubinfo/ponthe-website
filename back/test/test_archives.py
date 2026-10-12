import io
import itertools
import os
import shutil
import tempfile
import zipfile
from unittest import mock

from api import archives
from django.test import SimpleTestCase


class ArchiveTest(SimpleTestCase):
    """The zip of a selection: written in pieces, of a size known beforehand."""

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="ponthe-test-archives-")
        self.addCleanup(shutil.rmtree, self.folder, ignore_errors=True)

    def picture(self, name, size):
        path = os.path.join(self.folder, name)
        with open(path, "wb") as f:
            f.write(os.urandom(size))
        return name, path

    def test_the_announced_size_is_exact_on_both_sides_of_every_limit(self):
        # ZIP64 records appear past 2 GB or 65,535 files: the limits are
        # brought down to where a test can cross them.
        selections = [
            [self.picture("a.jpg", 1000)],
            [
                self.picture("été 100% ?.jpg", 300),
                self.picture("日本.png", 50),
                self.picture("empty.JPG", 0),
            ],
            [self.picture(f"photo-{i:02}.jpg", 37 * i) for i in range(30)],
        ]
        sizes = list(range(0, 400, 13)) + [900, 1000, 1049, 1050, 1051, 1100, 5000]
        sizes += [16000, 17000, 18000, zipfile.ZIP64_LIMIT]
        counts = [zipfile.ZIP_FILECOUNT_LIMIT, 2, 29, 30]
        cases = itertools.product(selections, sizes, counts)
        for pictures, size_limit, count_limit in cases:
            with mock.patch.object(zipfile, "ZIP64_LIMIT", size_limit):
                with mock.patch.object(zipfile, "ZIP_FILECOUNT_LIMIT", count_limit):
                    members = archives.members(pictures)
                    announced = archives.size(members)
                    data = b"".join(archives.write(members))
            with self.subTest(files=len(pictures), size=size_limit, count=count_limit):
                self.assertEqual(announced, len(data))
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    self.assertIsNone(archive.testzip())
                    self.assertEqual(archive.namelist(), [name for name, _ in pictures])
                    for name, path in pictures:
                        with open(path, "rb") as f:
                            self.assertEqual(archive.read(name), f.read())

    def test_the_archive_is_handed_over_in_small_pieces(self):
        members = archives.members([self.picture("heavy.jpg", 3 * archives.CHUNK)])
        self.assertEqual(archives.weight(members), 3 * archives.CHUNK)
        largest = max(len(piece) for piece in archives.write(members))
        self.assertLess(largest, archives.CHUNK + 1024)

    def test_a_picture_older_than_the_zip_format_still_goes_in(self):
        name, path = self.picture("old.jpg", 10)
        os.utime(path, (0, 0))  # 1970: zip dates start in 1980
        members = archives.members([(name, path)])
        data = b"".join(archives.write(members))
        self.assertEqual(archives.size(members), len(data))
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            self.assertEqual(archive.getinfo(name).date_time[0], 1980)
