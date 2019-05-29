from unittest.mock import patch
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from pulp_gem.app.serializers import GemContentSerializer

from pulpcore.plugin.models import Artifact


class TestGemContentSerializer(TestCase):
    """Test GemContentSerializer."""

    def setUp(self):
        """Set up the GemContentSerializer tests."""
        self.artifact = Artifact.objects.create(
            md5="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            sha1="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            sha224="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            sha256="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            sha384="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",  # noqa
            sha512="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",  # noqa
            size=1024,
            file=SimpleUploadedFile("test_filename_a", b"test content_a"),
        )
        self.artifact2 = Artifact.objects.create(
            md5="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            sha1="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            sha224="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            sha256="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            sha384="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",  # noqa
            sha512="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",  # noqa
            size=1024,
            file=SimpleUploadedFile("test_filename_b", b"test content_b"),
        )

    @patch("pulp_gem.app.serializers._artifact_from_data")
    @patch("pulp_gem.app.serializers.analyse_gem")
    def test_valid_data(self, ANALYZE_GEM, _ARTIFACT_FROM_DATA):
        """Test that the GemContentSerializer accepts valid data."""
        # Preparation
        ANALYZE_GEM.return_value = ("testname", "1.2.3-test", "---\n...")
        _ARTIFACT_FROM_DATA.return_value = self.artifact2
        data = {"artifact": "/pulp/api/v3/artifacts/{}/".format(self.artifact.pk)}
        serializer = GemContentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        # Verification
        ANALYZE_GEM.called_once_with(self.artifact)
        _ARTIFACT_FROM_DATA.called_once_with("---\n...")

    @patch("pulp_gem.app.serializers._artifact_from_data")
    @patch("pulp_gem.app.serializers.analyse_gem")
    def test_duplicate_data(self, ANALYZE_GEM, _ARTIFACT_FROM_DATA):
        """Test that the GemContentSerializer does not accept data."""
        # Preparation
        ANALYZE_GEM.return_value = ("testname", "1.2.3-test", "---\n...")
        _ARTIFACT_FROM_DATA.return_value = self.artifact2
        data = {"artifact": "/pulp/api/v3/artifacts/{}/".format(self.artifact.pk)}
        serializer = GemContentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        # Test
        serializer = GemContentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
