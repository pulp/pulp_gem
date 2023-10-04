from unittest.mock import patch
from django.test import TestCase
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from pulp_gem.app.serializers import GemContentSerializer

from pulpcore.plugin.models import Artifact

CHECKSUM_LEN = {
    "md5": 32,
    "sha1": 40,
    "sha224": 56,
    "sha256": 64,
    "sha384": 96,
    "sha512": 128,
}


def _checksums(char):
    return {name: char * CHECKSUM_LEN[name] for name in settings.ALLOWED_CONTENT_CHECKSUMS}


class TestGemContentSerializer(TestCase):
    """Test GemContentSerializer."""

    def setUp(self):
        """Set up the GemContentSerializer tests."""
        self.artifact = Artifact.objects.create(
            size=1024,
            file=SimpleUploadedFile("test_filename_a", b"test content_a"),
            **_checksums("a"),
        )
        self.artifact2 = Artifact.objects.create(
            size=1024,
            file=SimpleUploadedFile("test_filename_b", b"test content_b"),
            **_checksums("b"),
        )
        if settings.DOMAIN_ENABLED:
            self.V3_API_ROOT = settings.API_ROOT + "default/api/v3/"
        else:
            self.V3_API_ROOT = settings.V3_API_ROOT

    @patch("pulp_gem.app.serializers._artifact_from_data")
    @patch("pulp_gem.app.serializers.analyse_gem")
    def test_valid_data(self, ANALYZE_GEM, _ARTIFACT_FROM_DATA):
        """Test that the GemContentSerializer accepts valid data."""
        # Preparation
        ANALYZE_GEM.return_value = ({"name": "testname", "version": "1.2.3-test"}, "---\n...")
        _ARTIFACT_FROM_DATA.return_value = self.artifact2
        data = {"artifact": "{}artifacts/{}/".format(self.V3_API_ROOT, self.artifact.pk)}
        serializer = GemContentSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # Verification
        ANALYZE_GEM.called_once_with(self.artifact)
        _ARTIFACT_FROM_DATA.called_once_with("---\n...")

        # Test that the GemContentSerializer does accept duplicate data.
        serializer.save()
        serializer = GemContentSerializer(data=data)
        serializer.is_valid(raise_exception=True)
