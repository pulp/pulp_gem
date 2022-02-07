from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from pulpcore.plugin.actions import ModifyRepositoryActionMixin
from pulpcore.plugin.viewsets import (
    DistributionViewSet,
    ContentFilter,
    SingleArtifactContentUploadViewSet,
    OperationPostponedResponse,
    PublicationViewSet,
    RemoteViewSet,
    RepositoryViewSet,
    RepositoryVersionViewSet,
)
from pulpcore.plugin.serializers import (
    AsyncOperationResponseSerializer,
    RepositorySyncURLSerializer,
)
from pulpcore.plugin.tasking import enqueue_with_reservation

from pulp_gem.app import tasks
from pulp_gem.app.models import (
    GemContent,
    GemDistribution,
    GemRemote,
    GemPublication,
    GemRepository,
)
from pulp_gem.app.serializers import (
    GemContentSerializer,
    GemDistributionSerializer,
    GemPublicationSerializer,
    GemRemoteSerializer,
    GemRepositorySerializer,
)


class GemContentFilter(ContentFilter):
    """
    FilterSet for GemContent.
    """

    class Meta:
        model = GemContent
        fields = ["name", "version"]


class GemContentViewSet(SingleArtifactContentUploadViewSet):
    """
    A ViewSet for GemContent.
    """

    endpoint_name = "gem"
    queryset = GemContent.objects.prefetch_related("_artifacts")
    serializer_class = GemContentSerializer
    filterset_class = GemContentFilter


class GemRemoteViewSet(RemoteViewSet):
    """
    A ViewSet for GemRemote.
    """

    endpoint_name = "gem"
    queryset = GemRemote.objects.all()
    serializer_class = GemRemoteSerializer


class GemPublicationViewSet(PublicationViewSet):
    """
    A ViewSet for GemPublication.
    """

    endpoint_name = "gem"
    queryset = GemPublication.objects.exclude(complete=False)
    serializer_class = GemPublicationSerializer

    # This decorator is necessary since a publish operation is asyncrounous and returns
    # the id and href of the publish task.
    @extend_schema(
        description="Trigger an asynchronous task to publish gem content",
        responses={202: AsyncOperationResponseSerializer},
    )
    def create(self, request):
        """
        Publishes a repository.

        Either the ``repository`` or the ``repository_version`` fields can
        be provided but not both at the same time.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        repository_version = serializer.validated_data.get("repository_version")

        result = enqueue_with_reservation(
            tasks.publish,
            [repository_version.repository],
            kwargs={"repository_version_pk": str(repository_version.pk)},
        )
        return OperationPostponedResponse(result, request)


class GemRepositoryViewSet(RepositoryViewSet, ModifyRepositoryActionMixin):
    """
    A ViewSet for GemRepository.
    """

    endpoint_name = "gem"
    queryset = GemRepository.objects.all()
    serializer_class = GemRepositorySerializer

    # This decorator is necessary since a sync operation is asyncrounous and returns
    # the id and href of the sync task.
    @extend_schema(
        description="Trigger an asynchronous task to sync content.",
        summary="Sync from remote",
        responses={202: AsyncOperationResponseSerializer},
    )
    @action(detail=True, methods=["post"], serializer_class=RepositorySyncURLSerializer)
    def sync(self, request, pk):
        """
        Dispatches a sync task.
        """
        repository = self.get_object()
        serializer = RepositorySyncURLSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        remote = serializer.validated_data.get("remote")
        mirror = serializer.validated_data.get("mirror", True)

        result = enqueue_with_reservation(
            tasks.synchronize,
            [repository, remote],
            kwargs={"remote_pk": remote.pk, "repository_pk": repository.pk, "mirror": mirror},
        )
        return OperationPostponedResponse(result, request)


class GemRepositoryVersionViewSet(RepositoryVersionViewSet):
    """
    A ViewSet for a GemRepositoryVersion represents a single Gem repository version.
    """

    parent_viewset = GemRepositoryViewSet


class GemDistributionViewSet(DistributionViewSet):
    """
    ViewSet for GemDistributions.
    """

    endpoint_name = "gem"
    queryset = GemDistribution.objects.all()
    serializer_class = GemDistributionSerializer
