"""Tests that verify download of content served by Pulp."""
import pytest
import hashlib
from random import choice
from urllib.parse import urljoin

from pulp_gem.tests.functional.constants import DOWNLOAD_POLICIES, GEM_FIXTURE_URL


@pytest.mark.parametrize("policy", DOWNLOAD_POLICIES)
def test_download_content(
    policy,
    gem_repo,
    gem_repository_api_client,
    gem_content_api_client,
    gem_remote_factory,
    gem_publication_factory,
    gem_distribution_factory,
    http_get,
    download_content_unit,
    monitor_task,
    delete_orphans_pre,
):
    """Verify whether content served by pulp can be downloaded.

    Do the following:

    1. Create, populate, publish, and distribute a repository.
    2. Select a random content unit in the distribution. Download that
       content unit from Pulp, and verify that the content unit has the
       same checksum when fetched directly from Pulp-Fixtures.
    """
    remote = gem_remote_factory(policy=policy)

    # Sync repository
    body = {"remote": remote.pulp_href}
    result = gem_repository_api_client.sync(gem_repo.pulp_href, body)
    monitor_task(result.task)
    repo = gem_repository_api_client.read(gem_repo.pulp_href)

    # Create a publication.
    publication = gem_publication_factory(repository=gem_repo.pulp_href)

    # Create a distribution.
    distribution = gem_distribution_factory(publication=publication.pulp_href)

    # Pick a content unit, and download it from both Pulp Fixtures…
    content = gem_content_api_client.list(repository_version=repo.latest_version_href)
    content_paths = [f"gems/{c.name}-{c.version}.gem" for c in content.results]
    unit_path = choice(content_paths)
    fixtures_hash = hashlib.sha256(http_get(urljoin(GEM_FIXTURE_URL, unit_path))).hexdigest()

    # …and Pulp.
    content = download_content_unit(distribution.base_path, unit_path)
    pulp_hash = hashlib.sha256(content).hexdigest()

    assert fixtures_hash == pulp_hash
