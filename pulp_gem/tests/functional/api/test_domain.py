import pytest
from django.conf import settings

if not settings.DOMAIN_ENABLED:
    pytest.skip("Domains not enabled.", allow_module_level=True)


@pytest.mark.parallel
def test_domains(
    domain_factory,
    gem_remote_factory,
    gem_remote_api_client,
    gem_repository_factory,
    gem_repository_api_client,
    gem_publication_factory,
    gem_publication_api_client,
    gem_distribution_factory,
    gem_distribution_api_client,
):
    domain = domain_factory()
    domain_name = domain.name

    remote = gem_remote_factory(pulp_domain=domain_name)
    assert domain_name in remote.pulp_href
    result = gem_remote_api_client.list(pulp_domain=domain_name)
    assert result.count == 1

    repository = gem_repository_factory(pulp_domain=domain_name, remote=remote.pulp_href)
    assert domain_name in repository.pulp_href
    result = gem_repository_api_client.list(pulp_domain=domain_name)
    assert result.count == 1

    publication = gem_publication_factory(pulp_domain=domain_name, repository=repository.pulp_href)
    assert domain_name in publication.pulp_href
    result = gem_publication_api_client.list(pulp_domain=domain_name)
    assert result.count == 1

    distribution = gem_distribution_factory(
        pulp_domain=domain_name, publication=publication.pulp_href
    )
    assert domain_name in distribution.pulp_href
    result = gem_distribution_api_client.list(pulp_domain=domain_name)
    assert result.count == 1
