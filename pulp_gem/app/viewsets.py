import os

from gettext import gettext as _

from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import detail_route
from rest_framework import status
from rest_framework import serializers as rest_serializers
from rest_framework.response import Response

from pulpcore.app.files import PulpTemporaryUploadedFile
from pulpcore.plugin.models import Artifact, ContentArtifact
from pulpcore.plugin import viewsets as core
from pulpcore.plugin.serializers import (
    AsyncOperationResponseSerializer,
    RepositoryPublishURLSerializer,
    RepositorySyncURLSerializer,
)
from pulpcore.plugin.tasking import enqueue_with_reservation

from . import models, serializers, tasks

from ..specs import analyse_gem


class GemContentFilter(core.ContentFilter):
    """
    FilterSet for GemContent.
    """

    class Meta:
        model = models.GemContent
        fields = [
            'name',
            'version',
        ]


def _artifact_from_data(raw_data):
    tmpfile = PulpTemporaryUploadedFile("", "application/octet-stream", len(raw_data), "", "")
    tmpfile.write(raw_data)
    for hasher in Artifact.DIGEST_FIELDS:
        tmpfile.hashers[hasher].update(raw_data)

    artifact = Artifact()
    artifact.file = tmpfile
    artifact.size = tmpfile.size
    for hasher in Artifact.DIGEST_FIELDS:
        setattr(artifact, hasher, tmpfile.hashers[hasher].hexdigest())

    artifact.save()
    return artifact


class GemContentViewSet(core.ContentViewSet):
    """
    A ViewSet for GemContent.
    """

    endpoint_name = 'gem/gems'
    queryset = models.GemContent.objects.all()
    serializer_class = serializers.GemContentSerializer
    filterset_class = GemContentFilter

    @transaction.atomic
    def create(self, request):
        """
        Create GemContent from an artifact.
        """
        data = {}
        try:
            artifact = self.get_resource(request.data['artifact'], Artifact)
        except KeyError:
            raise rest_serializers.ValidationError(detail={'artifact': _('This field is required')})

        name, version, spec_data = analyse_gem(artifact.file.name)
        data['name'] = name
        data['version'] = version

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        content = serializer.save()

        relative_path = os.path.join('gems', name + '-' + version + '.gem')
        spec_relative_path = os.path.join('quick/Marshal.4.8', name + '-' + version + '.gemspec.rz')
        ContentArtifact(artifact=artifact,
                        content=content,
                        relative_path=relative_path).save()
        ContentArtifact(artifact=_artifact_from_data(spec_data),
                        content=content,
                        relative_path=spec_relative_path).save()

        headers = self.get_success_headers(request.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class GemRemoteViewSet(core.RemoteViewSet):
    """
    A ViewSet for GemRemote.
    """

    endpoint_name = 'gem'
    queryset = models.GemRemote.objects.all()
    serializer_class = serializers.GemRemoteSerializer

    # This decorator is necessary since a sync operation is asyncrounous and returns
    # the id and href of the sync task.
    @swagger_auto_schema(
        operation_description="Trigger an asynchronous task to sync gem content",
        responses={202: AsyncOperationResponseSerializer}
    )
    @detail_route(methods=('post',), serializer_class=RepositorySyncURLSerializer)
    def sync(self, request, pk):
        """
        Synchronizes a repository.

        The ``repository`` field has to be provided.
        """
        remote = self.get_object()
        serializer = RepositorySyncURLSerializer(data=request.data, context={'request': request})

        # Validate synchronously to return 400 errors.
        serializer.is_valid(raise_exception=True)
        repository = serializer.validated_data.get('repository')
        mirror = serializer.validated_data.get('mirror', True)
        result = enqueue_with_reservation(
            tasks.synchronize,
            [repository, remote],
            kwargs={
                'remote_pk': remote.pk,
                'repository_pk': repository.pk,
                'mirror': mirror,
            }
        )
        return core.OperationPostponedResponse(result, request)


class GemPublisherViewSet(core.PublisherViewSet):
    """
    A ViewSet for GemPublisher.
    """

    endpoint_name = 'gem'
    queryset = models.GemPublisher.objects.all()
    serializer_class = serializers.GemPublisherSerializer

    # This decorator is necessary since a publish operation is asyncrounous and returns
    # the id and href of the publish task.
    @swagger_auto_schema(
        operation_description="Trigger an asynchronous task to publish gem content",
        responses={202: AsyncOperationResponseSerializer}
    )
    @detail_route(methods=('post',), serializer_class=RepositoryPublishURLSerializer)
    def publish(self, request, pk):
        """
        Publishes a repository.

        Either the ``repository`` or the ``repository_version`` fields can
        be provided but not both at the same time.
        """
        publisher = self.get_object()
        serializer = RepositoryPublishURLSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        repository_version = serializer.validated_data.get('repository_version')

        result = enqueue_with_reservation(
            tasks.publish,
            [repository_version.repository, publisher],
            kwargs={
                'publisher_pk': str(publisher.pk),
                'repository_version_pk': str(repository_version.pk)
            }
        )
        return core.OperationPostponedResponse(result, request)
