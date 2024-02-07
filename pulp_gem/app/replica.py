from pulpcore.plugin.replica import Replicator

from pulp_glue.gem.context import (
    PulpGemDistributionContext,
    PulpGemPublicationContext,
    PulpGemRepositoryContext,
)

from pulp_gem.app.models import GemDistribution, GemRemote, GemRepository
from pulp_gem.app.tasks import synchronize as gem_synchronize


class GemReplicator(Replicator):
    repository_ctx_cls = PulpGemRepositoryContext
    distribution_ctx_cls = PulpGemDistributionContext
    publication_ctx_cls = PulpGemPublicationContext
    app_label = "gem"
    remote_model_cls = GemRemote
    repository_model_cls = GemRepository
    distribution_model_cls = GemDistribution
    distribution_serializer_name = "GemDistributionSerializer"
    repository_serializer_name = "GemRepositorySerializer"
    remote_serializer_name = "GemRemoteSerializer"
    sync_task = gem_synchronize

    def url(self, upstream_distribution):
        if upstream_distribution["publication"]:
            return upstream_distribution["base_url"]
        else:
            # This distribution doesn't serve any content
            return None

    def sync_params(self, repository, remote):
        return dict(
            remote_pk=str(remote.pk),
            repository_pk=str(repository.pk),
            mirror=True,
        )


REPLICATION_ORDER = [GemReplicator]
