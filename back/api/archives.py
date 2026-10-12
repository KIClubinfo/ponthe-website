"""
Zip of a selection of pictures, written as it is sent.

The archive is neither prepared on disk nor held in memory: each picture is
read and handed over in turn, so a whole gallery costs a worker no more than a
few hundred kilobytes, and nothing is left behind to clean up. Pictures are
stored, not deflated: a JPEG does not get any smaller.
"""

import zipfile

CHUNK = 256 * 1024


class Outbox:
    """Where zipfile writes. It has no seek(): zipfile then writes in one go."""

    def __init__(self):
        self.pieces = []

    def write(self, data):
        self.pieces.append(bytes(data))
        return len(data)

    def flush(self):
        pass

    def take(self):
        pieces, self.pieces = self.pieces, []
        return b"".join(pieces)


def members(pictures):
    """
    Turn (name, path) pairs into what the two functions below work from.

    The size of each file is read here, once: the announced size and the
    archive itself then agree on it.
    """
    return [
        (zipfile.ZipInfo.from_file(path, arcname=name, strict_timestamps=False), path)
        for name, path in pictures
    ]


def weight(members):
    return sum(info.file_size for info, _ in members)


def write(members):
    """Yield the archive piece by piece."""
    outbox = Outbox()
    with zipfile.ZipFile(outbox, "w", zipfile.ZIP_STORED) as archive:
        for info, path in members:
            with open(path, "rb") as source, archive.open(info, "w") as target:
                while chunk := source.read(CHUNK):
                    target.write(chunk)
                    yield outbox.take()
            yield outbox.take()
    yield outbox.take()


def size(members):
    """
    The number of bytes write() will produce, to the byte.

    Announcing it lets the browser show how far along the download is, and
    lets it tell a complete archive from one that was cut short. This follows
    what zipfile writes for stored members on a stream it cannot seek: a data
    descriptor after each one, and ZIP64 records past the limits. The tests
    compare it with real archives on both sides of every limit.
    """
    limit = zipfile.ZIP64_LIMIT
    position = 0
    directory = 0
    for info, _ in members:
        name = len(info.filename.encode("utf-8"))
        # zipfile decides on the size it was told, with a margin.
        large = info.file_size * 1.05 > limit
        fields = 2 * (info.file_size > limit) + (position > limit)
        directory += 46 + name + (4 + 8 * fields if fields else 0)
        position += 30 + name + (20 if large else 0)
        position += info.file_size + (24 if large else 16)
    end = 22
    if (
        len(members) > zipfile.ZIP_FILECOUNT_LIMIT
        or position > limit
        or directory > limit
    ):
        end += 56 + 20
    return position + directory + end
