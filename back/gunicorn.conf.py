import multiprocessing
import os

# Grab the number of desired workers from the environment or use Ncpu * 2 + 1
workers = os.environ.get(
    "GUNICORN_NB_WORKERS",
    multiprocessing.cpu_count() * 2 + 1,
)

max_requests = 400
# The longest requests read or write a whole gallery: the zip of a selection
# (up to DOWNLOAD_MAX_BYTES, at 40 MB/s or so when the disk is cold and less
# when several are read at once) and the extraction of an uploaded zip.
timeout = 300
keep_alive = 2

preload = True
