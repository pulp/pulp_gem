import pytest
import uuid

from pulpcore.client.pulp_gem import (
    ApiClient,
    ContentGemApi,
    DistributionsGemApi,
    PublicationsGemApi,
    RepositoriesGemApi,
    RepositoriesGemVersionsApi,
    RemotesGemApi,
)

from pulp_gem.tests.functional.constants import GEM_FIXTURE_URL

# Api Bindings fixtures


@pytest.fixture(scope="session")
def gem_client(_api_client_set, bindings_cfg):
    api_client = ApiClient(bindings_cfg)
    _api_client_set.add(api_client)
    yield api_client
    _api_client_set.remove(api_client)


@pytest.fixture(scope="session")
def gem_content_api_client(gem_client):
    return ContentGemApi(gem_client)


@pytest.fixture(scope="session")
def gem_distribution_api_client(gem_client):
    return DistributionsGemApi(gem_client)


@pytest.fixture(scope="session")
def gem_publication_api_client(gem_client):
    return PublicationsGemApi(gem_client)


@pytest.fixture(scope="session")
def gem_repository_api_client(gem_client):
    return RepositoriesGemApi(gem_client)


@pytest.fixture(scope="session")
def gem_repository_version_api_client(gem_client):
    return RepositoriesGemVersionsApi(gem_client)


@pytest.fixture(scope="session")
def gem_remote_api_client(gem_client):
    return RemotesGemApi(gem_client)


# Factory fixtures


@pytest.fixture(scope="class")
def gem_repository_factory(gem_repository_api_client, gen_object_with_cleanup):
    """A factory to generate a Gem Repository with auto-deletion after the test run."""

    def _gem_repository_factory(**kwargs):
        data = {"name": str(uuid.uuid4())}
        data.update(kwargs)
        return gen_object_with_cleanup(gem_repository_api_client, data)

    return _gem_repository_factory


@pytest.fixture(scope="class")
def gem_distribution_factory(gem_distribution_api_client, gen_object_with_cleanup):
    """A factory to generate a Gem Distribution with auto-deletion after the test run."""

    def _gem_distribution_factory(**body):
        data = {"base_path": str(uuid.uuid4()), "name": str(uuid.uuid4())}
        data.update(body)
        return gen_object_with_cleanup(gem_distribution_api_client, data)

    return _gem_distribution_factory


@pytest.fixture(scope="class")
def gem_publication_factory(gem_publication_api_client, gen_object_with_cleanup):
    """A factory to generate a Gem Publication with auto-deletion after the test run."""

    def _gem_publication_factory(**kwargs):
        # XOR check on repository and repository_version
        assert bool("repository" in kwargs) ^ bool("repository_version" in kwargs)
        return gen_object_with_cleanup(gem_publication_api_client, kwargs)

    return _gem_publication_factory


@pytest.fixture(scope="class")
def gem_remote_factory(gem_remote_api_client, gen_object_with_cleanup):
    """A factory to generate a Gem Remote with auto-deletion after the test run."""

    def _gem_remote_factory(*, url=GEM_FIXTURE_URL, policy="immediate", **kwargs):
        data = {"url": url, "policy": policy, "name": str(uuid.uuid4())}
        data.update(kwargs)
        return gen_object_with_cleanup(gem_remote_api_client, data)

    return _gem_remote_factory


@pytest.fixture
def gem_repo(gem_repository_factory):
    return gem_repository_factory()
