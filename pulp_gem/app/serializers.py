from rest_framework import serializers

from pulpcore.plugin.serializers import ContentSerializer, RemoteSerializer, \
    PublisherSerializer

from .models import GemContent, GemRemote, GemPublisher


class GemContentSerializer(ContentSerializer):
    """
    Serializer for Gem Content.
    """

    name = serializers.CharField(
        help_text='Name of the gem'
    )
    version = serializers.CharField(
        help_text='Version of the gem'
    )

    class Meta:
        fields = tuple(set(ContentSerializer.Meta.fields) - {'artifacts'}) + ('name', 'version')
        model = GemContent


class GemRemoteSerializer(RemoteSerializer):
    """
    Serializer for Gem Remotes.
    """

    class Meta:
        fields = RemoteSerializer.Meta.fields
        model = GemRemote


class GemPublisherSerializer(PublisherSerializer):
    """
    Serializer for Gem Publishers.
    """

    class Meta:
        fields = PublisherSerializer.Meta.fields
        model = GemPublisher
