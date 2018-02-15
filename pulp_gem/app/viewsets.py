from gettext import gettext as _

from django_filters.rest_framework import filterset
from rest_framework.decorators import detail_route
from rest_framework.exceptions import ValidationError

from pulpcore.plugin.models import Repository
from pulpcore.plugin.viewsets import (
    ContentViewSet,
    ImporterViewSet,
    OperationPostponedResponse,
    PublisherViewSet,
    tags)

from .models import GemContent, GemImporter, GemPublisher
from .serializers import GemContentSerializer, GemImporterSerializer, GemPublisherSerializer
from .tasks import publish, sync


class GemContentFilter(filterset.FilterSet):
    class Meta:
        model = GemContent
        fields = [
            'name',
            'version'
        ]


class GemContentViewSet(ContentViewSet):
    endpoint_name = 'gem'
    queryset = GemContent.objects.all()
    serializer_class = GemContentSerializer
    filter_class = GemContentFilter


class GemImporterViewSet(ImporterViewSet):
    endpoint_name = 'gem'
    queryset = GemImporter.objects.all()
    serializer_class = GemImporterSerializer

    @detail_route(methods=('post',))
    def sync(self, request, pk):
        importer = self.get_object()
        repository = self.get_resource(request.data['repository'], Repository)
        if not importer.feed_url:
            raise ValidationError(detail=_('A feed_url must be specified.'))

        result = sync.apply_async_with_reservation(
            tags.RESOURCE_REPOSITORY_TYPE, str(repository.pk),
            kwargs={
                'importer_pk': importer.pk,
                'repository_pk': repository.pk
            }
        )
        return OperationPostponedResponse([result], request)


class GemPublisherViewSet(PublisherViewSet):
    endpoint_name = 'gem'
    queryset = GemPublisher.objects.all()
    serializer_class = GemPublisherSerializer

    @detail_route(methods=('post',))
    def publish(self, request, pk):
        publisher = self.get_object()
        repository = self.get_resource(request.data['repository'], Repository)
        result = publish.apply_async_with_reservation(
            tags.RESOURCE_REPOSITORY_TYPE, str(repository.pk),
            kwargs={
                'publisher_pk': str(publisher.pk),
                'repository_pk': repository.pk
            }
        )
        return OperationPostponedResponse([result], request)
