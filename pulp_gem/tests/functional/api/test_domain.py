import pytest
from django.conf import settings

if not settings.DOMAIN_ENABLED:
    pytest.skip("Domains not enabled.", allow_module_level=True)


@pytest.mark.parallel
def test_domains(
    gem_bindings,
    domain_factory,
    gem_remote_factory,
    gem_repository_factory,
    gem_publication_factory,
    gem_distribution_factory,
):
    domain = domain_factory()
    domain_name = domain.name

    remote = gem_remote_factory(pulp_domain=domain_name)
    assert domain_name in remote.pulp_href
    result = gem_bindings.RemotesGemApi.list(pulp_domain=domain_name)
    assert result.count == 1

    repository = gem_repository_factory(pulp_domain=domain_name, remote=remote.pulp_href)
    assert domain_name in repository.pulp_href
    result = gem_bindings.RepositoriesGemApi.list(pulp_domain=domain_name)
    assert result.count == 1

    publication = gem_publication_factory(pulp_domain=domain_name, repository=repository.pulp_href)
    assert domain_name in publication.pulp_href
    result = gem_bindings.PublicationsGemApi.list(pulp_domain=domain_name)
    assert result.count == 1

    distribution = gem_distribution_factory(
        pulp_domain=domain_name, publication=publication.pulp_href
    )
    assert domain_name in distribution.pulp_href
    result = gem_bindings.DistributionsGemApi.list(pulp_domain=domain_name)
    assert result.count == 1
