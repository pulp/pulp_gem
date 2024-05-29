"""Tests that publish gem plugin repositories."""

import pytest
from random import choice


@pytest.mark.parallel
def test_publish(
    gem_bindings,
    gem_publication_factory,
    gem_remote_factory,
    gem_repository_factory,
    monitor_task,
):
    """Test whether a particular repository version can be published.

    1. Create a repository with at least 2 repository versions.
    2. Create a publication by supplying the latest ``repository_version``.
    3. Assert that the publication ``repository_version`` attribute points
       to the latest repository version.
    4. Create a publication by supplying the non-latest ``repository_version``.
    5. Assert that the publication ``repository_version`` attribute points
       to the supplied repository version.
    """
    repository = gem_repository_factory()
    remote = gem_remote_factory()
    result = gem_bindings.RepositoriesGemApi.sync(
        repository.pulp_href, {"remote": remote.pulp_href}
    )
    monitor_task(result.task)
    repository = gem_bindings.RepositoriesGemApi.read(repository.pulp_href)

    # Step 1
    content = gem_bindings.ContentGemApi.list(repository_version=repository.latest_version_href)
    for i, gem_content in enumerate(content.results):
        repo_ver_href = f"{repository.versions_href}{i}/"
        body = {"add_content_units": [gem_content.pulp_href], "base_version": repo_ver_href}
        result = gem_bindings.RepositoriesGemApi.modify(repository.pulp_href, body)
        monitor_task(result.task)

    repository = gem_bindings.RepositoriesGemApi.read(repository.pulp_href)
    assert repository.latest_version_href.endswith(f"/{content.count + 1}/")

    versions = gem_bindings.RepositoriesGemVersionsApi.list(repository.pulp_href)
    # This is in descending order, so latest first
    version_hrefs = [ver.pulp_href for ver in versions.results]
    non_latest = choice(version_hrefs[:-1])

    # Step 2
    publication = gem_publication_factory(repository=repository.pulp_href)

    # Step 3
    assert publication.repository_version == version_hrefs[0]

    # Step 4
    publication = gem_publication_factory(repository_version=non_latest)

    # Step 5
    assert publication.repository_version == non_latest
