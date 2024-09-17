import logging

from aiohttp import ClientConnectionError
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
    PRERELEASE_VERSION_REGEX,
    read_versions,
    read_info,
    ruby_ver_includes,
    split_ext_version,
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
        remote_url = self.remote.url

        # Read filters from remote
        includes = self.remote.includes
        excludes = self.remote.excludes
        prereleases = self.remote.prereleases

        async with ProgressReport(
            message="Downloading versions list", total=1
        ) as pr_download_versions:
            versions_url = urljoin(remote_url, "versions")
            versions_downloader = self.remote.get_downloader(url=versions_url)
            try:
                versions_result = await versions_downloader.run()
            except ClientConnectionError as e:
                raise Exception(f"Could not connect to host {e.host}")
            await pr_download_versions.aincrement()

        async with ProgressReport(message="Parsing versions list") as pr_parse_versions:
            async with ProgressReport(message="Parsing versions info") as pr_parse_info:
                async for name, ext_versions, md5_sum in read_versions(versions_result.path):
                    await pr_parse_versions.aincrement()

                    # Skip conditions based on the gem name
                    # =====================================
                    if not NAME_REGEX.fullmatch(name):
                        log.warn(f"Skipping invalid gem name: '{name}'.")
                        continue
                    if includes is not None:
                        if name not in includes:
                            continue
                        include_versions = includes[name]
                    else:
                        include_versions = None
                    if excludes is not None and name in excludes:
                        exclude_versions = excludes[name]
                        if exclude_versions is None:
                            continue
                    else:
                        exclude_versions = None

                    # Skip conditions based on the gem version
                    # ========================================

                    # Keep a list to track the skipped versions for logging.
                    kept_versions = set(ext_versions)
                    # The list 'ext_versions' contains "{version}[-{platform}]" entries!
                    # This dict is like a set of ext_versions with payload dict on
                    # {version, platform, prerelease}.
                    versions_info = {
                        ext_version: split_ext_version(ext_version) for ext_version in ext_versions
                    }
                    # Sanitize versions.
                    versions_info = {
                        k: v
                        for k, v in versions_info.items()
                        if PRERELEASE_VERSION_REGEX.fullmatch(v["version"])
                    }
                    if len(kept_versions) > len(versions_info):
                        log.warn(
                            _("Skipped invalid versions for '%s': %s"),
                            name,
                            kept_versions - set(versions_info.keys()),
                        )
                        kept_versions = set(versions_info.keys())

                    if not prereleases:
                        # Prerelease versions are already sanitized.
                        # But for the sake of logging we handle them differently.
                        versions_info = {
                            k: v for k, v in versions_info.items() if not v["prerelease"]
                        }
                        if len(kept_versions) > len(versions_info):
                            log.debug(
                                _("Skipped prerelease versions for '%s': %s"),
                                name,
                                kept_versions - set(versions_info.keys()),
                            )
                            kept_versions = set(versions_info.keys())

                    if include_versions is not None:
                        versions_info = {
                            k: v
                            for k, v in versions_info.items()
                            if ruby_ver_includes(include_versions, v["version"])
                        }
                        if len(kept_versions) > len(versions_info):
                            log.debug(
                                _("Skipped versions for '%s' include filter: %s"),
                                name,
                                kept_versions - set(versions_info.keys()),
                            )
                            kept_versions = set(versions_info.keys())

                    if exclude_versions is not None:
                        versions_info = {
                            k: v
                            for k, v in versions_info.items()
                            if not ruby_ver_includes(exclude_versions, v["version"])
                        }
                        if len(kept_versions) > len(versions_info):
                            log.debug(
                                _("Skipped versions for '%s' exclude filter: %s"),
                                name,
                                kept_versions - set(versions_info.keys()),
                            )
                            kept_versions = set(versions_info.keys())

                    if not versions_info:
                        log.debug(_("No version left for '%s'; skip reading the info file."), name)
                        continue

                    info_url = urljoin(urljoin(self.remote.url, "info/"), name)
                    if "md5" in settings.ALLOWED_CONTENT_CHECKSUMS:
                        extra_kwargs = {"expected_digests": {"md5": md5_sum}}
                    elif md5_sum is None:
                        extra_kwargs = {}
                        log.warn(f"Checksum of info file for '{name}' was not provided.")
                    else:
                        extra_kwargs = {}
                        log.warn(f"Checksum of info file for '{name}' could not be validated.")
                    info_downloader = self.remote.get_downloader(url=info_url, **extra_kwargs)
                    info_result = await info_downloader.run()
                    async for gem_info in read_info(info_result.path, versions_info):
                        gem_info["name"] = name
                        gem = GemContent(**gem_info)
                        gem_path = gem.relative_path
                        gem_url = urljoin(remote_url, gem_path)
                        gemspec_path = gem.gemspec_path
                        gemspec_url = urljoin(remote_url, gemspec_path)

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
