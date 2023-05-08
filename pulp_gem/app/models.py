from logging import getLogger

from django.db import models, utils
from pathlib import PurePath
from tempfile import NamedTemporaryFile

from pulpcore.plugin.models import (
    Artifact,
    Content,
    Publication,
    Distribution,
    Remote,
    Repository,
)

from pulp_gem.specs import analyse_gem


log = getLogger(__name__)


class GemContent(Content):
    """
    The "gem" content type.

    Content of this type represents a ruby gem file
    with its spec data.

    Fields:
        name (str): The name of the gem.
        version (str): The version of the gem.

    """

    TYPE = "gem"

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

    @staticmethod
    def init_from_artifact_and_relative_path(artifact, relative_path):
        """"""
        name, version, spec_data = analyse_gem(artifact.file)
        content = GemContent(name=name, version=version)
        relative_path = content.relative_path

        with NamedTemporaryFile(mode="wb", dir=".", delete=False) as temp_file:
            temp_file.write(spec_data)
            temp_file.flush()

        spec_artifact = Artifact.init_and_validate(temp_file.name)
        try:
            spec_artifact.save()
        except utils.IntegrityError:
            spec_artifact = Artifact.objects.get(spec_artifact.q())
            spec_artifact.touch()
        spec_relative_path = content.gemspec_path

        artifacts = {relative_path: artifact, spec_relative_path: spec_artifact}
        return content, artifacts

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"
        unique_together = ("name", "version")


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
    CONTENT_TYPES = [GemContent]
    REMOTE_TYPES = [GemRemote]

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"
