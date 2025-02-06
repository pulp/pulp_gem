"""Tests that sync gem plugin repositories."""

import pytest

from pulp_gem.tests.functional.constants import (
    DOWNLOAD_POLICIES,
    GEM_FIXTURE_SUMMARY,
    GEM_INVALID_FIXTURE_URL,
    GEM_FIXTURE_URL,
)
from pulpcore.tests.functional.utils import PulpTaskError


@pytest.fixture
def do_sync(gem_bindings, gem_repository_factory, gem_remote_factory, monitor_task):
    """Factory fixture to perform a sync."""

    def _do_sync(repo=None, remote=None, url=GEM_FIXTURE_URL, policy="immediate"):
        if repo is None:
            repo = gem_repository_factory()

        if repo.remote is None:
            if remote is None:
                remote = gem_remote_factory(url=url, policy=policy)
            sync_args = {"remote": remote.pulp_href}
        else:
            sync_args = {}

        result = gem_bindings.RepositoriesGemApi.sync(repo.pulp_href, sync_args)
        monitor_task(result.task)
        repo = gem_bindings.RepositoriesGemApi.read(repo.pulp_href)
        return repo, remote

    return _do_sync


@pytest.mark.parallel
@pytest.mark.parametrize("download_policy", DOWNLOAD_POLICIES)
def test_download_policies(
    gem_bindings,
    download_policy,
    do_sync,
    monitor_task,
):
    """Sync repositories with the different ``download_policy``.

    Do the following:

    1. Create a repository, and a remote.
    2. Assert that repository version is None.
    3. Sync the remote.
    4. Assert that repository version is not None.
    5. Assert that the correct number of possible units to be downloaded
       were shown.
    6. Sync the remote one more time
    7. Assert that repository version is the same from the previous one.
    """
    repo, remote = do_sync(policy=download_policy)

    assert repo.latest_version_href.endswith("/1/")
    repo_ver = gem_bindings.RepositoriesGemVersionsApi.read(repo.latest_version_href)
    present_summary = {k: v["count"] for k, v in repo_ver.content_summary.present.items()}
    assert present_summary == GEM_FIXTURE_SUMMARY
    added_summary = {k: v["count"] for k, v in repo_ver.content_summary.added.items()}
    assert added_summary == GEM_FIXTURE_SUMMARY

    # Sync the repository again.
    update_task = gem_bindings.RepositoriesGemApi.partial_update(
        repo.pulp_href, {"remote": remote.pulp_href}
    ).task
    monitor_task(update_task)
    repo = gem_bindings.RepositoriesGemApi.read(repo.pulp_href)
    repo2, _ = do_sync(repo=repo, remote=remote)
    assert repo2.latest_version_href == repo.latest_version_href


@pytest.mark.parallel
def test_invalid_url(do_sync):
    """Sync a repository using a remote url that does not exist."""
    with pytest.raises(PulpTaskError) as exc:
        # This url is an actual website...
        do_sync(url="http://i-am-an-invalid-url.com/invalid/")
    # TODO fix sync to give a proper error when an invalid url is passed
    assert exc.value.task.error["description"] is not None


# Provide an invalid repository and specify keywords in the anticipated error message
@pytest.mark.skip("FIXME: Plugin writer action required.")
def test_invalid_plugin_template_content(do_sync):
    """Sync a repository using an invalid plugin_content repository.

    Assert that an exception is raised, and that error message has
    keywords related to the reason of the failure.
    """
    with pytest.raises(PulpTaskError) as exc:
        do_sync(url=GEM_INVALID_FIXTURE_URL)
    assert "Some invalid message" in exc.value.task.to_dict()["error"]["description"]
