import datetime
import gzip
import hashlib
import logging
import os
import shutil

from gettext import gettext as _

from django.conf import settings
from django.core.files import File
from django.db import transaction
from jinja2 import Template
from pathlib import Path

from pulpcore.plugin.models import (
    ContentArtifact,
    RepositoryVersion,
    PublishedArtifact,
    PublishedMetadata,
)

from pulp_gem.app.models import GemContent, GemPublication
from pulp_gem.specs import ruby_ver_cmp, write_specs, GemKey


log = logging.getLogger(__name__)


index_template = """<!DOCTYPE html>
<html>
  <head>
    {% if path -%}
    <title>Index of {{ path }}</title>
    {% else -%}
    <title>Gem Index</title>
    {% endif -%}
  </head>
  <body>
    <a href="../">../</a><br/>
    {% for link in links %}
    <a href="{{ link|e }}">{{ link|e }}</a><br/>
    {% endfor %}
  </body>
</html>
"""


def _publish_specs(specs, relative_path, publication):
    write_specs(specs, relative_path)
    with open(relative_path, "rb") as f_in:
        with gzip.open(relative_path + ".gz", "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    PublishedMetadata.create_from_file(
        publication=publication, file=File(open(relative_path, "rb"))
    )
    PublishedMetadata.create_from_file(
        publication=publication, file=File(open(relative_path + ".gz", "rb"))
    )


def _publish_compact_index(lines, relative_path, publication, timestamp=False, with_list=False):
    with open(relative_path, "w") as fp:
        if timestamp:
            timestamp = datetime.datetime.utcnow().isoformat(timespec="seconds")
            fp.write(f"created_at: {timestamp}Z\n")
        fp.write("---\n")
        for line in lines:
            fp.write(line + "\n")
    metadata = PublishedMetadata.create_from_file(
        publication=publication, file=File(open(relative_path, "rb"))
    )
    if with_list:
        with transaction.atomic():
            list_path = relative_path + ".list"
            pm = PublishedMetadata.objects.create(relative_path=list_path, publication=publication)
            ca = ContentArtifact.objects.create(
                relative_path=list_path, content=pm, artifact=metadata._artifacts.first()
            )
            PublishedArtifact.objects.create(
                relative_path=list_path, content_artifact=ca, publication=publication
            )
    return metadata


def _create_index(publication, path="", links=None):
    links = links or []
    links = (li if li.endswith("/") else str(Path(li).relative_to(path)) for li in links)
    template = Template(index_template)
    index_path = f"{path}index.html"
    if path:
        Path(path).mkdir(exist_ok=True)
    with open(index_path, "w") as index:
        index.write(template.render(links=links, path=path))

    return PublishedMetadata.create_from_file(
        relative_path=index_path, publication=publication, file=File(open(index_path, "rb"))
    )


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
    with GemPublication.create(repository_version, pass_through=True) as publication:
        specs = []
        latest_versions = {}
        prerelease_specs = []
        gems = []
        gemspecs = []
        for content in (
            GemContent.objects.filter(pk__in=publication.repository_version.content)
            .only("name", "version", "platform", "prerelease")
            .order_by("-pulp_created")
            .iterator()
        ):
            if content.prerelease:
                prerelease_specs.append(GemKey(content.name, content.version, content.platform))
            else:
                specs.append(GemKey(content.name, content.version, content.platform))
                old_ver = latest_versions.get((content.name, content.platform))
                if old_ver is None or ruby_ver_cmp(old_ver, content.version) < 0:
                    latest_versions[(content.name, content.platform)] = content.version
            gems.append(content.relative_path)
            gemspecs.append(content.gemspec_path)
        latest_specs = [
            GemKey(name, ver, platform) for (name, platform), ver in latest_versions.items()
        ]

        _publish_specs(specs, "specs.4.8", publication)
        _publish_specs(latest_specs, "latest_specs.4.8", publication)
        _publish_specs(prerelease_specs, "prerelease_specs.4.8", publication)

        # compact_index
        gems_qs = GemContent.objects.filter(pk__in=publication.repository_version.content)
        names_qs = gems_qs.order_by("name").values_list("name", flat=True).distinct()
        _publish_compact_index(names_qs, "names", publication, with_list=True)

        versions_lines = []
        os.mkdir("info")
        for name in names_qs:
            lines = []
            version_list = []
            for gem in gems_qs.filter(name=name):
                deps = ",".join((f"{key}:{value}" for key, value in gem.dependencies.items()))
                line = f"{gem.ext_version} {deps}|checksum:{gem.checksum}"
                if gem.required_ruby_version:
                    line += f",ruby:{gem.required_ruby_version}"
                if gem.required_rubygems_version:
                    line += f",rubygems:{gem.required_rubygems_version}"
                lines.append(line)
                version_list.append(gem.ext_version)
            info_metadata = _publish_compact_index(lines, f"info/{name}", publication)
            versions = ",".join(version_list)
            if "md5" in settings.ALLOWED_CONTENT_CHECKSUMS:
                md5_sum = info_metadata._artifacts.first().md5
            else:
                artifact = info_metadata._artifacts.first()
                artifact.file.seek(0)
                md5_sum = hashlib.md5(artifact.file.read()).hexdigest()
            versions_lines.append(f"{name} {versions} {md5_sum}")
        _publish_compact_index(
            versions_lines, "versions", publication, timestamp=True, with_list=True
        )

        _create_index(
            publication,
            path="",
            links=[
                "gems/",
                "quick/Marshal.4.8/",
                "specs.4.8",
                "latest_specs.4.8",
                "prerelease_specs.4.8",
                "names",
                "names.list",
                "versions",
                "versions.list",
                "info/",
            ],
        )
        _create_index(publication, path="gems/", links=gems)
        _create_index(publication, path="quick/", links=["quick/Marshal.4.8/"])
        _create_index(publication, path="quick/Marshal.4.8/", links=gemspecs)
        _create_index(publication, path="info/", links=(f"info/{name}" for name in names_qs))

    log.info(_("Publication: {publication} created").format(publication=publication.pk))
