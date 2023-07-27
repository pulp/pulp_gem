from logging import getLogger

from pathlib import PurePath
from tempfile import NamedTemporaryFile
from django.contrib.postgres.fields import HStoreField
from django.db import models

from pulpcore.plugin.models import (
    Content,
    Publication,
    Distribution,
    Remote,
    Repository,
)

from pulp_gem.specs import analyse_gem


log = getLogger(__name__)


class ShallowGemContent(Content):
    """
    The "shallow-gem" content type.

    Content of this type represents a ruby gem file with its spec data.
    This is the old deprecated format that is only carried around for legacy installations.

    Fields:
        name (str): The name of the gem.
        version (str): The version of the gem.

    """

    TYPE = "shallow-gem"

    name = models.TextField(blank=False, null=False)
    version = models.TextField(blank=False, null=False)

    @property
    def relative_path(self):
        """The relative path this gem is stored under for the content app."""
        return f"gems/{self.name}-{self.version}.gem"

    @property
    def gemspec_path(self):
        """The path for this gem's gemspec for the content app."""
        return f"quick/Marshal.4.8/{self.name}-{self.version}.gemspec.rz"

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"
        unique_together = ("name", "version")


class GemContent(Content):
    """
    The "gem" content type.

    Content of this type represents a ruby gem file
    with its spec data.
    """

    TYPE = "gem"
    repo_key_fields = ("name", "version", "platform")

    name = models.TextField(blank=False, null=False)
    version = models.TextField(blank=False, null=False)
    # `null` on `platform is allowed for zero downtime upgrade from version 0.1.*.
    # Change this to `null=False` in a version no earlier than 0.3.0.
    # See also `ext_version` and the datarepair-gemspec-platform command.
    platform = models.TextField(blank=False, null=True)
    checksum = models.CharField(max_length=64, null=False, db_index=True)
    prerelease = models.BooleanField(default=False)
    dependencies = HStoreField(default=dict)
    required_ruby_version = models.TextField(null=True)
    required_rubygems_version = models.TextField(null=True)

    @property
    def relative_path(self):
        """The relative path this gem is stored under for the content app."""
        return f"gems/{self.name}-{self.ext_version}.gem"

    @property
    def gemspec_path(self):
        """The path for this gem's gemspec for the content app."""
        return f"quick/Marshal.4.8/{self.name}-{self.ext_version}.gemspec.rz"

    @property
    def ext_version(self):
        """The version for this gem with the appended platform if not "ruby"."""
        # Remove the `None` with the change to the platform column.
        if self.platform is None or self.platform == "ruby":
            platform_suffix = ""
        else:
            platform_suffix = f"-{self.platform}"
        return f"{self.version}{platform_suffix}"

    @staticmethod
    def init_from_artifact_and_relative_path(artifact, relative_path):
        gem_info, spec_data = analyse_gem(artifact.file)
        gem_info["checksum"] = artifact.sha256
        content = GemContent(**gem_info)
        relative_path = content.relative_path

        with NamedTemporaryFile(mode="wb", dir=".", delete=False) as temp_file:
            temp_file.write(spec_data)
            temp_file.flush()

        spec_relative_path = content.gemspec_path

        # Spec artifact will be on-demand at this point
        artifacts = {relative_path: artifact, spec_relative_path: None}
        return content, artifacts

    def __str__(self):
        return f"<GemContent {self.name}-{self.ext_version}>"

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"
        unique_together = ("checksum",)


class GemDistribution(Distribution):
    """
    A Distribution for GemContent.
    """

    TYPE = "gem"

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"


class GemPublication(Publication):
    """
    A Publication for GemContent.
    """

    TYPE = "gem"

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"


class GemRemote(Remote):
    """
    A Remote for GemContent.
    """

    TYPE = "gem"

    prereleases = models.BooleanField(default=False)
    includes = HStoreField(null=True)
    excludes = HStoreField(null=True)

    def get_remote_artifact_content_type(self, relative_path=None):
        """
        Return a modified GemContent class that has a reference to this remote.

        This will ensure that GemContent.init_from_artifact_and_relative_path can properly create
        the Remote Artifact for the second Artifact it needs whether that be the gem file or the
        gemspec.
        """
        if relative_path:
            path = PurePath(relative_path)
            if path.match("gems/*.gem"):
                return GemContent
        return None

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"


class GemRepository(Repository):
    """
    A Repository for GemContent.
    """

    TYPE = "gem"
    CONTENT_TYPES = [GemContent, ShallowGemContent]
    REMOTE_TYPES = [GemRemote]

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"
