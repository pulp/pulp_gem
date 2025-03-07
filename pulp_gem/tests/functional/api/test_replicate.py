import pytest
import uuid


@pytest.mark.parallel
def test_replication(
    pulpcore_bindings,
    gem_bindings,
    domain_factory,
    bindings_cfg,
    monitor_task,
    monitor_task_group,
    pulp_settings,
    add_to_cleanup,
    gen_object_with_cleanup,
    gem_distribution_factory,
    gem_publication_factory,
    gem_repository_factory,
    gem_content_artifact,
):
    # This test assures that an Upstream Pulp can be created in a non-default domain and that this
    # Upstream Pulp configuration can be used to execute the replicate task.

    # Create a domain to replicate from
    source_domain = domain_factory()

    # Create a domain as replica
    replica_domain = domain_factory()

    # Add stuff to it
    repository = gem_repository_factory(pulp_domain=source_domain.name)
    content_response = gem_bindings.ContentGemApi.create(
        file=str(gem_content_artifact),
        repository=repository.pulp_href,
        pulp_domain=source_domain.name,
    )
    monitor_task(content_response.task)
    publication = gem_publication_factory(
        pulp_domain=source_domain.name, repository=repository.pulp_href
    )
    gem_distribution_factory(pulp_domain=source_domain.name, publication=publication.pulp_href)

    # Create an Upstream Pulp in the non-default domain
    upstream_pulp_body = {
        "name": str(uuid.uuid4()),
        "base_url": bindings_cfg.host,
        "api_root": pulp_settings.API_ROOT,
        "domain": source_domain.name,
        "username": bindings_cfg.username,
        "password": bindings_cfg.password,
        "tls_validation": False,
    }
    upstream_pulp = gen_object_with_cleanup(
        pulpcore_bindings.UpstreamPulpsApi, upstream_pulp_body, pulp_domain=replica_domain.name
    )
    # Run the replicate task and assert that all tasks successfully complete.
    response = pulpcore_bindings.UpstreamPulpsApi.replicate(upstream_pulp.pulp_href)
    monitor_task_group(response.task_group)

    for api_client in (
        gem_bindings.DistributionsGemApi,
        gem_bindings.RemotesGemApi,
        gem_bindings.RepositoriesGemApi,
    ):
        result = api_client.list(pulp_domain=replica_domain.name)
        for item in result.results:
            add_to_cleanup(api_client, item)

    for api_client in (
        gem_bindings.DistributionsGemApi,
        gem_bindings.RemotesGemApi,
        gem_bindings.RepositoriesGemApi,
        gem_bindings.ContentGemApi,
    ):
        result = api_client.list(pulp_domain=replica_domain.name)
        assert result.count == 1
