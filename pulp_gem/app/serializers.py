from rest_framework import serializers

from pulpcore.plugin.serializers import ContentSerializer, ImporterSerializer, PublisherSerializer

from .models import GemContent, GemImporter, GemPublisher


class GemContentSerializer(ContentSerializer):
    name = serializers.CharField()
    version = serializers.CharField()

    class Meta:
        fields = ContentSerializer.Meta.fields + ('name', 'version')
        model = GemContent


class GemImporterSerializer(ImporterSerializer):

    sync_mode = serializers.ChoiceField(
        help_text='How the importer should sync from the upstream repository.',
        allow_blank=False,
        choices=[GemImporter.ADDITIVE, GemImporter.MIRROR],
    )

    class Meta:
        fields = ImporterSerializer.Meta.fields
        model = GemImporter


class GemPublisherSerializer(PublisherSerializer):
    class Meta:
        fields = PublisherSerializer.Meta.fields
        model = GemPublisher
