import shutil
import tempfile

from django.test.runner import DiscoverRunner
from django.test.utils import override_settings


class TempMediaRunner(DiscoverRunner):
    """
    Runs the tests on a throwaway media folder.

    Importing, zipping and deleting pictures all touch MEDIA_ROOT. Whatever a
    test does, now or later, it must never reach the real folder — the suite
    is also run where that folder holds the galleries.
    """

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self.media_root = tempfile.mkdtemp(prefix="ponthe-test-media-")
        self.media_override = override_settings(MEDIA_ROOT=self.media_root)
        self.media_override.enable()

    def teardown_test_environment(self, **kwargs):
        self.media_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)
        super().teardown_test_environment(**kwargs)
