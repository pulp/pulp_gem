import logging
import re
import gzip
import shutil

from gettext import gettext as _
from packaging import version

from django.core.files import File

from pulpcore.plugin.models import RepositoryVersion, PublishedArtifact, PublishedMetadata
from pulpcore.plugin.tasking import WorkingDirectory

from pulp_gem.app.models import GemContent, GemPublication
from pulp_gem.specs import write_specs, Key


log = logging.getLogger(__name__)


def _publish_specs(specs, relative_path, publication):
    write_specs(specs, relative_path)
    with open(relative_path, "rb") as f_in:
        with gzip.open(relative_path + ".gz", "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    specs_metadata = PublishedMetadata.create_from_file(
        publication=publication, file=File(open(relative_path, "rb"))
    )
    specs_metadata.save()
    specs_metadata_gz = PublishedMetadata.create_from_file(
        publication=publication, file=File(open(relative_path + ".gz", "rb"))
    )
    specs_metadata_gz.save()


def publish(repository_version_pk):
    """
    Create a Publication based on a RepositoryVersion.

    Args:
        repository_version_pk (str): Create a publication from this repository version.

    """
    repository_version = RepositoryVersion.objects.get(pk=repository_version_pk)

    log.info(
        _("Publishing: repository={repo}, version={ver}").format(
            repo=repository_version.repository.name, ver=repository_version.number
        )
    )
    with WorkingDirectory():
        with GemPublication.create(repository_version) as publication:
            specs = []
            latest_versions = {}
            prerelease_specs = []
            for content in GemContent.objects.filter(
                pk__in=publication.repository_version.content
            ).order_by("-pulp_created"):
                for content_artifact in content.contentartifact_set.all():
                    published_artifact = PublishedArtifact(
                        relative_path=content_artifact.relative_path,
                        publication=publication,
                        content_artifact=content_artifact,
                    )
                    published_artifact.save()
                if re.fullmatch(r"[0-9.]*", content.version):
                    specs.append(Key(content.name, content.version))
                    old_ver = latest_versions.get(content.name)
                    if old_ver is None or version.parse(old_ver) < version.parse(content.version):
                        latest_versions[content.name] = content.version
                else:
                    prerelease_specs.append(Key(content.name, content.version))
            latest_specs = [Key(name, version) for name, version in latest_versions.items()]

            _publish_specs(specs, "specs.4.8", publication)
            _publish_specs(latest_specs, "latest_specs.4.8", publication)
            _publish_specs(prerelease_specs, "prerelease_specs.4.8", publication)

    log.info(_("Publication: {publication} created").format(publication=publication.pk))
