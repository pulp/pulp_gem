import pytest
import subprocess
from aiohttp.client_exceptions import ClientResponseError


def test_pull_through_metadata(
    gem_remote_factory,
    gem_distribution_factory,
    gem_content_api_client,
    artifacts_api_client,
    http_get,
):
    """
    Test that pull-through caching can retrieve metadata files upstream, but does not save them.
    """
    artifacts_before = artifacts_api_client.list().count
    content_before = gem_content_api_client.list().count

    # Choose a remote source that supports all the different gem repository metadata formats
    remote = gem_remote_factory(url="https://rubygems.org")
    distribution = gem_distribution_factory(remote=remote.pulp_href)

    urls = [
        "info/pulp_file_client",
        "specs.4.8",
        "latest_specs.4.8",
        "prerelease_specs.4.8",
        "quick/Marshal.4.8/pulp_file_client-1.14.0.gemspec.rz",
    ]
    for path in urls:
        url = distribution.base_url + path
        assert http_get(url)

    artifacts_after = artifacts_api_client.list().count
    content_after = gem_content_api_client.list().count

    assert artifacts_before == artifacts_after
    assert content_before == content_after

    with pytest.raises(ClientResponseError) as e:
        http_get(distribution.base_url + "NOT_A_VALID_LINK")

    assert e.value.status == 404


def test_pull_through_install(
    gem_remote_factory, gem_distribution_factory, gem_content_api_client, delete_orphans_pre
):
    """
    Test that gem clients can install from a distribution with pull-through caching.
    """
    out = subprocess.run(("which", "gem"))
    if out.returncode != 0:
        pytest.skip("gem not installed on test machine")
    content_before = gem_content_api_client.list().count

    remote = gem_remote_factory(url="https://rubygems.org")
    distribution = gem_distribution_factory(remote=remote.pulp_href)

    remote2 = gem_remote_factory()
    distribution2 = gem_distribution_factory(remote=remote2.pulp_href)

    for dis, gem in ((distribution, "a"), (distribution2, "beryl")):
        cmd = ["gem", "i", "--remote", "--clear-sources", "-s", dis.base_url, gem, "-v", "0.1.0"]

        out = subprocess.run(cmd, stdout=subprocess.PIPE)
        assert f"Successfully installed {gem}-0.1.0" in out.stdout.decode("utf-8")

        r = gem_content_api_client.list(name=gem, version="0.1.0")
        assert r.count == 1
        assert r.results[0].name == gem
        assert r.results[0].version == "0.1.0"

        subprocess.run(("gem", "uninstall", gem, "-v", "0.1.0"))

    content_after = gem_content_api_client.list().count
    assert content_before + 2 == content_after
