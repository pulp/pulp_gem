import logging
import re
import gzip
import shutil

from gettext import gettext as _
from packaging import version

from django.core.files import File
from jinja2 import Template
from pathlib import Path

from pulpcore.plugin.models import RepositoryVersion, PublishedMetadata

from pulp_gem.app.models import GemContent, GemPublication
from pulp_gem.specs import write_specs, Key


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
    specs_metadata = PublishedMetadata.create_from_file(
        publication=publication, file=File(open(relative_path, "rb"))
    )
    specs_metadata.save()
    specs_metadata_gz = PublishedMetadata.create_from_file(
        publication=publication, file=File(open(relative_path + ".gz", "rb"))
    )
    specs_metadata_gz.save()


def _create_index(publication, path="", links=None):
    links = links or []
    links = (li if li.endswith("/") else str(Path(li).relative_to(path)) for li in links)
    template = Template(index_template)
    index_path = f"{path}index.html"
    if path:
        Path(path).mkdir(exist_ok=True)
    with open(index_path, "w") as index:
        index.write(template.render(links=links, path=path))

    index_metadata = PublishedMetadata.create_from_file(
        relative_path=index_path, publication=publication, file=File(open(index_path, "rb"))
    )
    index_metadata.save()


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
            .only("name", "version")
            .order_by("-pulp_created")
            .iterator()
        ):
            if re.fullmatch(r"[0-9.]*", content.version):
                specs.append(Key(content.name, content.version))
                old_ver = latest_versions.get(content.name)
                if old_ver is None or version.parse(old_ver) < version.parse(content.version):
                    latest_versions[content.name] = content.version
            else:
                prerelease_specs.append(Key(content.name, content.version))
            gems.append(content.relative_path)
            gemspecs.append(content.gemspec_path)
        latest_specs = [Key(name, ver) for name, ver in latest_versions.items()]

        _publish_specs(specs, "specs.4.8", publication)
        _publish_specs(latest_specs, "latest_specs.4.8", publication)
        _publish_specs(prerelease_specs, "prerelease_specs.4.8", publication)
        _create_index(
            publication,
            path="",
            links=[
                "gems/",
                "quick/Marshal.4.8/",
                "specs.4.8",
                "latest_specs.4.8",
                "prerelease_specs.4.8",
            ],
        )
        _create_index(publication, path="gems/", links=gems)
        _create_index(publication, path="quick/", links=[])
        _create_index(publication, path="quick/Marshal.4.8/", links=gemspecs)

    log.info(_("Publication: {publication} created").format(publication=publication.pk))
