import logging
import os
import re
import gzip

from collections import namedtuple
from gettext import gettext as _
from urllib.parse import urlparse, urlunparse
from packaging import version

from celery import shared_task
from django.core.files import File
from django.db.models import Q

from pulpcore.plugin.models import (
    Artifact,
    RepositoryVersion,
    Repository)
from pulpcore.plugin.changeset import (
    BatchIterator,
    ChangeSet,
    PendingArtifact,
    PendingContent,
    SizedIterable)
from pulpcore.plugin.tasking import UserFacingTask, WorkingDirectory

from pulp_gem.app.models import GemContent, GemRemote
from pulp_gem.specs import Specs, Key


log = logging.getLogger(__name__)


# The set of Key to be added and removed.
Delta = namedtuple('Delta', ('additions', 'removals'))


@shared_task(base=UserFacingTask)
def synchronize(remote_pk, repository_pk):
    """
    Create a new version of the repository that is synchronized with the remote
    as specified by the remote.

    Args:
        remote_pk (str): The remote PK.
        repository_pk (str): The repository PK.

    Raises:
        ValueError: When feed_url is empty.
    """
    remote = GemRemote.objects.get(pk=remote_pk)
    repository = Repository.objects.get(pk=repository_pk)
    base_version = RepositoryVersion.latest(repository)

    if not remote.url:
        raise ValueError(_('A remote must have a url specified to synchronize.'))

    with WorkingDirectory():
        with RepositoryVersion.create(repository) as new_version:
            log.info(
                _('Synchronizing: repository=%(r)s remote=%(p)s'),
                {
                    'r': repository.name,
                    'p': remote.name
                })
            specs = fetch_specs(remote)
            content = fetch_content(base_version)
            delta = find_delta(specs, content)
            additions = build_additions(remote, specs, delta)
            removals = build_removals(base_version, delta)
            changeset = ChangeSet(
                remote=remote,
                repository_version=new_version,
                additions=additions,
                removals=removals)
            for report in changeset.apply():
                if not log.isEnabledFor(logging.DEBUG):
                    continue
                log.debug(
                    _('Applied: repository=%(r)s remote=%(p)s change:%(c)s'),
                    {
                        'r': repository.name,
                        'p': remote.name,
                        'c': report,
                    })


def fetch_specs(remote):
    """
    Fetch (download) the specs (specs.4.8.gz and [TODO] prerelease_specs.4.8.gz).
    """
    parsed_url = urlparse(remote.url)
    root_dir = os.path.dirname(parsed_url.path)

    specs_path = os.path.join(root_dir, 'specs.4.8.gz')
    downloader = remote.get_downloader(urlunparse(parsed_url._replace(path=specs_path)))
    downloader.fetch()
    specs = Specs()
    with gzip.open(downloader.path, 'rb') as fd:
        specs.read(fd)
    return specs


def fetch_content(base_version):
    """
    Fetch the GemContent contained in the (base) repository version.

    Args:
        base_version (RepositoryVersion): A repository version.

    Returns:
        set: A set of Key contained in the (base) repository version.
    """
    content = set()
    if base_version:
        for gem in GemContent.objects.filter(pk__in=base_version.content):
            key = Key(name=gem.name, version=gem.version)
            content.add(key)
    return content


def find_delta(specs, content, mirror=True):
    """
    Using the specs and set of existing (natural) keys,
    determine the set of content to be added and deleted from the
    repository.  Expressed in natural key.
    """
    """
    Find the content that needs to be added and removed.

    Args:
        specs (Specs): The downloaded specs.
        content: (set): The set of natural keys for content contained in the (base)
            repository version.
        mirror (bool): The delta should include changes needed to ensure the content
            contained within the pulp repository is exactly the same as the
            content contained within the remote repository.

    Returns:
        Delta: The set of Key to be added and removed.
    """
    remote_content = set(
        [
            Key(name=e.name, version=e.version) for e in specs
        ])
    additions = (remote_content - content)
    if mirror:
        removals = (content - remote_content)
    else:
        removals = set()
    return Delta(additions, removals)


def build_additions(remote, specs, delta):
    """
    Build the content to be added.

    Args:
        remote (FileRemote): A remote.
        specs (Specs): The downloaded specs.
        delta (Delta): The set of Key to be added and removed.

    Returns:
        SizedIterable: The PendingContent to be added to the repository.
    """
    def generate():
        for key in delta.additions:
            relative_path = os.path.join('gems', key.name + '-' + key.version + '.gem')
            path = os.path.join(root_dir, relative_path)
            url = urlunparse(parsed_url._replace(path=path))

            spec_relative_path = os.path.join('quick/Marshal.4.8', key.name + '-' + key.version + '.gemspec.rz')
            spec_path = os.path.join(root_dir, spec_relative_path)
            spec_url = urlunparse(parsed_url._replace(path=spec_path))

            gem = GemContent(name=key.name, version=key.version)
            content = PendingContent(
                gem,
                artifacts={
                    PendingArtifact(Artifact(), url, relative_path),
                    PendingArtifact(Artifact(), spec_url, spec_relative_path),
                })
            yield content
    parsed_url = urlparse(remote.url)
    root_dir = os.path.dirname(parsed_url.path)
    return SizedIterable(generate(), len(delta.additions))

def build_removals(base_version, delta):
    """
    Build the content to be removed.

    Args:
        base_version (RepositoryVersion):  The base repository version.
        delta (Delta): The set of Key to be added and removed.

    Returns:
        SizedIterable: The FileContent to be removed from the repository.
    """
    def generate():
        for removals in BatchIterator(delta.removals):
            q = Q()
            for key in removals:
                q |= Q(gemcontent__name=key.name, gemcontent__version=key.version)
            q_set = self._base_version.content.filter(q)
            q_set = q_set.only('id')
            for gem in q_set:
                yield gem
    return SizedIterable(generate(), len(delta.removals))
