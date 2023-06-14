import logging

from gettext import gettext as _
from urllib.parse import urljoin

from django.conf import settings

from pulpcore.plugin.models import Artifact, ProgressReport, Remote, Repository
from pulpcore.plugin.stages import (
    DeclarativeArtifact,
    DeclarativeContent,
    DeclarativeVersion,
    Stage,
)

from pulp_gem.app.models import GemContent, GemRemote
from pulp_gem.specs import (
    NAME_REGEX,
    VERSION_REGEX,
    PRERELEASE_VERSION_REGEX,
    read_versions,
    read_info,
    ruby_ver_includes,
)


log = logging.getLogger(__name__)


def synchronize(remote_pk, repository_pk, mirror=False):
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
    dv = DeclarativeVersion(first_stage, repository, mirror=mirror)
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

        async with ProgressReport(
            message="Downloading versions list", total=1
        ) as pr_download_versions:
            versions_url = urljoin(self.remote.url, "versions")
            versions_downloader = self.remote.get_downloader(url=versions_url)
            versions_result = await versions_downloader.run()
            await pr_download_versions.aincrement()

        async with ProgressReport(message="Parsing versions list") as pr_parse_versions:
            async with ProgressReport(message="Parsing versions info") as pr_parse_info:
                async for name, versions, md5_sum in read_versions(versions_result.path):
                    await pr_parse_versions.aincrement()
                    if not NAME_REGEX.match(name):
                        log.warn(f"Skipping invalid gem name: '{name}'.")
                        continue
                    if not self.remote.prereleases:
                        versions = [version for version in versions if VERSION_REGEX.match(version)]
                    else:
                        versions = [
                            version
                            for version in versions
                            if PRERELEASE_VERSION_REGEX.match(version)
                        ]
                    if self.remote.includes:
                        if name not in self.remote.includes:
                            continue
                        version_requirements = self.remote.includes[name]
                        if version_requirements is not None:
                            versions = [
                                version
                                for version in versions
                                if ruby_ver_includes(version_requirements, version)
                            ]
                    if self.remote.excludes:
                        if name in self.remote.excludes:
                            version_requirements = self.remote.excludes[name]
                            if version_requirements is None:
                                continue
                            versions = [
                                version
                                for version in versions
                                if not ruby_ver_includes(version_requirements, version)
                            ]
                    if not versions:
                        continue
                    info_url = urljoin(urljoin(self.remote.url, "info/"), name)
                    if "md5" in settings.ALLOWED_CONTENT_CHECKSUMS:
                        extra_kwargs = {"expected_digests": {"md5": md5_sum}}
                    else:
                        extra_kwargs = {}
                        log.warn(f"Checksum of info file for '{name}' could not be validated.")
                    info_downloader = self.remote.get_downloader(url=info_url, **extra_kwargs)
                    info_result = await info_downloader.run()
                    async for gem_info in read_info(info_result.path, versions):
                        gem_info["name"] = name
                        gem = GemContent(**gem_info)
                        gem_path = gem.relative_path
                        gem_url = urljoin(self.remote.url, gem_path)
                        gemspec_path = gem.gemspec_path
                        gemspec_url = urljoin(self.remote.url, gemspec_path)

                        da_gem = DeclarativeArtifact(
                            artifact=Artifact(sha256=gem_info["checksum"]),
                            url=gem_url,
                            relative_path=gem_path,
                            remote=self.remote,
                            deferred_download=deferred_download,
                        )
                        da_gemspec = DeclarativeArtifact(
                            artifact=Artifact(),
                            url=gemspec_url,
                            relative_path=gemspec_path,
                            remote=self.remote,
                            deferred_download=deferred_download,
                        )
                        dc = DeclarativeContent(content=gem, d_artifacts=[da_gem, da_gemspec])
                        await pr_parse_info.aincrement()
                        await self.put(dc)
