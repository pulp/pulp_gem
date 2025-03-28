import uuid

import pytest
from pulpcore.tests.functional.utils import BindingsNamespace
from pulp_gem.tests.functional.constants import GEM_FIXTURE_URL, GEM_URL

# Api Bindings fixtures


@pytest.fixture(scope="session")
def gem_bindings(_api_client_set, bindings_cfg):
    """
    A namespace providing preconfigured pulp_gem api clients.

    e.g. `gem_bindings.RepositoriesGemApi.list()`.
    """
    from pulpcore.client import pulp_gem as bindings_module

    api_client = bindings_module.ApiClient(bindings_cfg)
    _api_client_set.add(api_client)
    yield BindingsNamespace(bindings_module, api_client)
    _api_client_set.remove(api_client)


# Factory fixtures


@pytest.fixture(scope="class")
def gem_repository_factory(gem_bindings, gen_object_with_cleanup):
    """A factory to generate a Gem Repository with auto-deletion after the test run."""

    def _gem_repository_factory(**kwargs):
        extra_args = {}
        if pulp_domain := kwargs.pop("pulp_domain", None):
            extra_args["pulp_domain"] = pulp_domain
        data = {"name": str(uuid.uuid4())}
        data.update(kwargs)
        return gen_object_with_cleanup(gem_bindings.RepositoriesGemApi, data, **extra_args)

    return _gem_repository_factory


@pytest.fixture(scope="class")
def gem_distribution_factory(gem_bindings, gen_object_with_cleanup):
    """A factory to generate a Gem Distribution with auto-deletion after the test run."""

    def _gem_distribution_factory(**kwargs):
        extra_args = {}
        if pulp_domain := kwargs.pop("pulp_domain", None):
            extra_args["pulp_domain"] = pulp_domain
        data = {"base_path": str(uuid.uuid4()), "name": str(uuid.uuid4())}
        data.update(kwargs)
        return gen_object_with_cleanup(gem_bindings.DistributionsGemApi, data, **extra_args)

    return _gem_distribution_factory


@pytest.fixture(scope="class")
def gem_publication_factory(gem_bindings, gen_object_with_cleanup):
    """A factory to generate a Gem Publication with auto-deletion after the test run."""

    def _gem_publication_factory(**kwargs):
        extra_args = {}
        if pulp_domain := kwargs.pop("pulp_domain", None):
            extra_args["pulp_domain"] = pulp_domain
        # XOR check on repository and repository_version
        assert bool("repository" in kwargs) ^ bool("repository_version" in kwargs)
        return gen_object_with_cleanup(gem_bindings.PublicationsGemApi, kwargs, **extra_args)

    return _gem_publication_factory


@pytest.fixture(scope="class")
def gem_remote_factory(gem_bindings, gen_object_with_cleanup):
    """A factory to generate a Gem Remote with auto-deletion after the test run."""

    def _gem_remote_factory(*, url=GEM_FIXTURE_URL, policy="immediate", **kwargs):
        extra_args = {}
        if pulp_domain := kwargs.pop("pulp_domain", None):
            extra_args["pulp_domain"] = pulp_domain
        data = {"url": url, "policy": policy, "name": str(uuid.uuid4())}
        data.update(kwargs)
        return gen_object_with_cleanup(gem_bindings.RemotesGemApi, data, **extra_args)

    return _gem_remote_factory


@pytest.fixture(scope="session")
def gem_content_artifact(tmp_path_factory, http_get):
    """A file containing amber-1.0.0.gem."""

    temp_file = tmp_path_factory.mktemp("pulp_gem") / "amber-1.0.0.gem"
    content = http_get(GEM_URL)
    temp_file.write_bytes(content)
    return temp_file
