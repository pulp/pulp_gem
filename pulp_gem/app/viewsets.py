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
from pulpcore.plugin.tasking import dispatch

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
        fields = ["name", "version", "checksum", "prerelease"]


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

        result = dispatch(
            tasks.publish,
            exclusive_resources=[repository_version.repository],
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

    @extend_schema(
        description="Trigger an asynchronous task to sync gem content.",
        summary="Sync from a remote",
        responses={202: AsyncOperationResponseSerializer},
    )
    @action(detail=True, methods=["post"], serializer_class=RepositorySyncURLSerializer)
    def sync(self, request, pk):
        """
        Dispatches a sync task.
        """
        serializer = RepositorySyncURLSerializer(
            data=request.data, context={"request": request, "repository_pk": pk}
        )
        serializer.is_valid(raise_exception=True)

        repository = self.get_object()
        remote = serializer.validated_data.get("remote", repository.remote)
        mirror = serializer.validated_data.get("mirror", True)

        result = dispatch(
            tasks.synchronize,
            shared_resources=[remote],
            exclusive_resources=[repository],
            kwargs={
                "remote_pk": str(remote.pk),
                "repository_pk": str(repository.pk),
                "mirror": mirror,
            },
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
