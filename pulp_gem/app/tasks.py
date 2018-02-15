import logging
import os
import re
import gzip
import shutil
import rubymarshal.classes
import rubymarshal.writer
import rubymarshal.reader

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
    Publication,
    PublishedArtifact,
    PublishedMetadata,
    Repository)
from pulpcore.plugin.changeset import (
    BatchIterator,
    ChangeSet,
    PendingArtifact,
    PendingContent,
    SizedIterable)
from pulpcore.plugin.tasking import UserFacingTask, WorkingDirectory

from pulp_gem.app.models import GemContent, GemImporter, GemPublisher


log = logging.getLogger(__name__)


# Natural key.
Key = namedtuple('Key', ('name', 'version'))


class Specs(list):
    def read(self, fd):
        data = rubymarshal.reader.load(fd)
        for item in data:
            name = item[0]
            if name.__class__ is bytes:
                name = name.decode()
            version = item[1].values[0]
            if version.__class__ is bytes:
                version = version.decode()
            self.append(Key(name, version))

    def write(self, fd):
        specs = [[e.name, rubymarshal.classes.UsrMarshal('Gem::Version', [e.version]), 'ruby']
                 for e in self]
        rubymarshal.writer.write(fd, specs)


def _publish_specs(specs, relative_path, publication):
    with open(relative_path, 'wb') as fd:
        specs.write(fd)
    with open(relative_path, 'rb') as f_in:
        with gzip.open(relative_path + '.gz', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    specs_metadata = PublishedMetadata(
        relative_path=relative_path,
        publication=publication,
        file=File(open(relative_path, 'rb')))
    specs_metadata.save()
    specs_metadata_gz = PublishedMetadata(
        relative_path=relative_path + '.gz',
        publication=publication,
        file=File(open(relative_path + '.gz', 'rb')))
    specs_metadata_gz.save()


@shared_task(base=UserFacingTask)
def publish(publisher_pk, repository_pk):
    """
    Use provided publisher to create a Publication based on a RepositoryVersion.

    Args:
        publisher_pk (str): Use the publish settings provided by this publisher.
        repository_pk (str): Create a Publication from the latest version of this Repository.
    """
    publisher = GemPublisher.objects.get(pk=publisher_pk)
    repository = Repository.objects.get(pk=repository_pk)
    repository_version = RepositoryVersion.latest(repository)

    log.info(
        _('Publishing: repository=%(repository)s, version=%(version)d, publisher=%(publisher)s'),
        {
            'repository': repository.name,
            'version': repository_version.number,
            'publisher': publisher.name,
        })

    with WorkingDirectory():
        with Publication.create(repository_version, publisher) as publication:
            specs = Specs()
            latest_versions = {}
            prerelease_specs = Specs()
            for content in GemContent.objects.filter(
                    pk__in=publication.repository_version.content).order_by('-created'):
                for content_artifact in content.contentartifact_set.all():
                    published_artifact = PublishedArtifact(
                        relative_path=content_artifact.relative_path,
                        publication=publication,
                        content_artifact=content_artifact)
                    published_artifact.save()
                if re.fullmatch(r"[0-9.]*", content.version):
                    specs.append(Key(content.name, content.version))
                    old_ver = latest_versions.get(content.name)
                    if old_ver is None or version.parse(old_ver) < version.parse(content.version):
                        latest_versions[content.name] = content.version
                else:
                    prerelease_specs.append(Key(content.name, content.version))
            latest_specs = Specs(Key(name, version) for name, version in latest_versions.items())

            _publish_specs(specs, 'specs.4.8', publication)
            _publish_specs(latest_specs, 'latest_specs.4.8', publication)
            _publish_specs(prerelease_specs, 'prerelease_specs.4.8', publication)

    log.info(
        _('Publication: %(publication)s created'),
        {
            'publication': publication.pk
        })


@shared_task(base=UserFacingTask)
def sync(importer_pk, repository_pk):
    """
    Validate the importer, create and finalize RepositoryVersion.

    Args:
        importer_pk (str): The importer PK.
        repository_pk (str): The repository to sync into.

    Raises:
        ValueError: When feed_url is empty.
    """
    importer = GemImporter.objects.get(pk=importer_pk)
    repository = Repository.objects.get(pk=repository_pk)

    if not importer.feed_url:
        raise ValueError(_("An importer must have a 'feed_url' attribute to sync."))

    base_version = RepositoryVersion.latest(repository)

    with RepositoryVersion.create(repository) as new_version:

        synchronizer = Synchronizer(importer, new_version, base_version)
        with WorkingDirectory():
            log.info(
                _('Starting sync: repository=%(repository)s importer=%(importer)s'),
                {
                    'repository': repository.name,
                    'importer': importer.name
                })
            synchronizer.run()


class Synchronizer:
    """
    Repository synchronizer for GemContent

    This object walks through the full standard workflow of running a sync. See the "run" method
    for details on that workflow.
    """

    def __init__(self, importer, new_version, base_version):
        """
        Args:
            importer (Importer): the importer to use for the sync operation
            new_version (pulpcore.plugin.models.RepositoryVersion): the new version to which content
                should be added and removed.
            base_version (pulpcore.plugin.models.RepositoryVersion): the latest version
                or None if one does not exist.
        """
        self._importer = importer
        self._new_version = new_version
        self._base_version = base_version
        self._specs = Specs()
        self._prerelease_specs = Specs()
        self._inventory_keys = set()
        self._keys_to_add = set()
        self._keys_to_remove = set()

    def run(self):
        """
        Synchronize the repository with the remote repository.

        This walks through the standard workflow that most sync operations want to follow. This
        pattern is a recommended starting point for other plugins.

        - Determine what is available remotely.
        - Determine what is already in the local repository.
        - Compare those two, and based on any importer settings or content-type-specific logic,
          figure out what you want to add and remove from the local repository.
        - Use a ChangeSet to make those changes happen.
        """
        # Determine what is available remotely
        self._fetch_specs()
        # Determine what is already in the repo
        self._fetch_inventory()

        # Based on the above two, figure out what we want to add and remove
        self._find_delta()
        additions = SizedIterable(
            self._build_additions(),
            len(self._keys_to_add))
        removals = SizedIterable(
            self._build_removals(),
            len(self._keys_to_remove))

        # Hand that to a ChangeSet, and we're done!
        changeset = ChangeSet(self._importer, self._new_version, additions=additions,
                              removals=removals)
        changeset.apply_and_drain()

    def _fetch_specs(self):
        """
        Fetch (download) the specs (specs.4.8.gz and [TODO] prerelease_specs.4.8.gz).
        """
        parsed_url = urlparse(self._importer.feed_url)
        root_dir = os.path.dirname(parsed_url.path)

        specs_path = os.path.join(root_dir, 'specs.4.8.gz')
        downloader = self._importer.get_downloader(urlunparse(parsed_url._replace(path=specs_path)))
        downloader.fetch()
        with gzip.open(downloader.path, 'rb') as fd:
            self._specs.read(fd)

    def _fetch_inventory(self):
        """
        Fetch existing content in the repository.
        """
        # it's not a problem if there is no pre-existing version.
        if self._base_version is not None:
            for content in GemContent.objects.filter(pk__in=self._base_version.content):
                key = Key(name=content.name, version=content.version)
                self._inventory_keys.add(key)

    def _find_delta(self):
        """
        Using the specs and set of existing (natural) keys,
        determine the set of content to be added and deleted from the
        repository.  Expressed in natural key.
        """
        # These keys are available remotely. Storing just the natural key makes it memory-efficient
        # and thus reasonable to hold in RAM even with a large number of content units.
        remote_keys = set([Key(name=e.name, version=e.version) for e in self._specs])

        self._keys_to_add = remote_keys - self._inventory_keys
        if self._importer.sync_mode == GemImporter.MIRROR:
            self._keys_to_remove = self._inventory_keys - remote_keys

    def _build_additions(self):
        """
        Generate the content to be added.

        Returns:
            generator: A generator of content to be added.
        """
        parsed_url = urlparse(self._importer.feed_url)
        root_dir = os.path.dirname(parsed_url.path)

        for key in self._keys_to_add:
            # Instantiate the content and artifact based on the key values.
            gem = GemContent(name=key.name, version=key.version)

            relative_path = os.path.join('gems', key.name + '-' + key.version + '.gem')
            path = os.path.join(root_dir, relative_path)
            url = urlunparse(parsed_url._replace(path=path))

            spec_relative_path = os.path.join('quick/Marshal.4.8', key.name + '-' + key.version + '.gemspec.rz')
            spec_path = os.path.join(root_dir, spec_relative_path)
            spec_url = urlunparse(parsed_url._replace(path=spec_path))

            # Now that we know what we want to add, hand it to "core" with the API objects.
            content = PendingContent(
                gem,
                artifacts={
                    PendingArtifact(Artifact(), url, relative_path),
                    PendingArtifact(Artifact(), spec_url, spec_relative_path),
                })
            yield content

    def _build_removals(self):
        """
        Generate the content to be removed.

        Returns:
            generator: A generator of GemContent instances to remove from the repository
        """
        for natural_keys in BatchIterator(self._keys_to_remove):
            q = Q()
            for key in natural_keys:
                q |= Q(gemcontent__name=key.name, gemcontent__version=key.version)
            q_set = self._base_version.content.filter(q)
            q_set = q_set.only('id')
            for content in q_set:
                yield content
