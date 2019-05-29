import logging
import os

from gettext import gettext as _
from urllib.parse import urlparse, urlunparse

from pulpcore.plugin.models import Artifact, ProgressReport, Remote, Repository
from pulpcore.plugin.stages import (
    DeclarativeArtifact,
    DeclarativeContent,
    DeclarativeVersion,
    Stage,
    ArtifactDownloader,
    ArtifactSaver,
    QueryExistingContents,
    ContentSaver,
    RemoteArtifactSaver,
)

from pulp_gem.app.models import GemContent, GemRemote
from pulp_gem.specs import read_specs


log = logging.getLogger(__name__)


class UpdateExistingContentArtifacts(Stage):
    """
    Stage to update declarative_artifacts from existing content.

    A Stages API stage that sets existing
    :class:`~pulpcore.plugin.models.Artifact` in
    :class:`~pulpcore.plugin.stages.DeclarativeArtifact` instances from
    :class:`~pulpcore.plugin.stages.DeclarativeContent` units if the respective
    :class:`~pulpcore.plugin.models.Content` is already existing.
    """

    async def run(self):
        """
        The coroutine for this stage.

        Returns:
            The coroutine for this stage.

        """
        async for d_content in self.items():
            if d_content.content.pk is not None:
                for d_artifact in d_content.d_artifacts:
                    content_artifact = d_content.content.contentartifact_set.get(
                        relative_path=d_artifact.relative_path
                    )
                    if content_artifact.artifact is not None:
                        d_artifact.artifact = content_artifact.artifact
            await self.put(d_content)


def synchronize(remote_pk, repository_pk, mirror):
    """
    Create a new version of the repository that is synchronized with the remote as specified.

    Args:
        remote_pk (str): The remote PK.
        repository_pk (str): The repository PK.
        mirror (bool): True for mirror mode, False for additive.

    Raises:
        ValueError: If the remote does not specify a URL to sync.

    """
    remote = GemRemote.objects.get(pk=remote_pk)
    repository = Repository.objects.get(pk=repository_pk)

    if not remote.url:
        raise ValueError(_("A remote must have a url specified to synchronize."))

    first_stage = GemFirstStage(remote)
    dv = GemDeclarativeVersion(first_stage, repository, mirror=mirror)
    dv.create()


class GemFirstStage(Stage):
    """
    The first stage of a pulp_gem sync pipeline.
    """

    def __init__(self, remote):
        """
        The first stage of a pulp_gem sync pipeline.

        Args:
            remote (GemRemote): The remote data to be used when syncing

        """
        self.remote = remote

    async def run(self):
        """
        Build and emit `DeclarativeContent` from the Spec data.
        """
        # Interpret policy to download Artifacts or not
        deferred_download = self.remote.policy != Remote.IMMEDIATE

        with ProgressReport(message="Downloading Metadata") as progress:
            parsed_url = urlparse(self.remote.url)
            root_dir = parsed_url.path
            specs_path = os.path.join(root_dir, "specs.4.8.gz")
            specs_url = urlunparse(parsed_url._replace(path=specs_path))
            downloader = self.remote.get_downloader(url=specs_url)
            result = await downloader.run()
            progress.increment()

        with ProgressReport(message="Parsing Metadata") as progress:
            for key in read_specs(result.path):
                relative_path = os.path.join("gems", key.name + "-" + key.version + ".gem")
                path = os.path.join(root_dir, relative_path)
                url = urlunparse(parsed_url._replace(path=path))

                spec_relative_path = os.path.join(
                    "quick/Marshal.4.8", key.name + "-" + key.version + ".gemspec.rz"
                )
                spec_path = os.path.join(root_dir, spec_relative_path)
                spec_url = urlunparse(parsed_url._replace(path=spec_path))
                gem = GemContent(name=key.name, version=key.version)
                da_gem = DeclarativeArtifact(
                    artifact=Artifact(),
                    url=url,
                    relative_path=relative_path,
                    remote=self.remote,
                    deferred_download=deferred_download,
                )
                da_spec = DeclarativeArtifact(
                    artifact=Artifact(),
                    url=spec_url,
                    relative_path=spec_relative_path,
                    remote=self.remote,
                    deferred_download=deferred_download,
                )
                dc = DeclarativeContent(content=gem, d_artifacts=[da_gem, da_spec])
                progress.increment()
                await self.put(dc)


class GemDeclarativeVersion(DeclarativeVersion):
    """
    Custom implementation of Declarative version.
    """

    def pipeline_stages(self, new_version):
        """
        Build the list of pipeline stages feeding into the ContentUnitAssociation stage.

        This is overwritten to create a custom pipeline.

        Args:
            new_version (:class:`~pulpcore.plugin.models.RepositoryVersion`): The
                new repository version that is going to be built.

        Returns:
            list: List of :class:`~pulpcore.plugin.stages.Stage` instances

        """
        pipeline = [
            self.first_stage,
            QueryExistingContents(),
            UpdateExistingContentArtifacts(),
            ArtifactDownloader(),
            ArtifactSaver(),
            ContentSaver(),
            RemoteArtifactSaver(),
        ]
        return pipeline
