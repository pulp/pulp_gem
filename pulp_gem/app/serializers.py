from rest_framework import serializers
from pulpcore.plugin import serializers as platform

from . import models


class GemContentSerializer(platform.ContentSerializer):
    """
    A Serializer for GemContent.
    """

    name = serializers.CharField(
        help_text='Name of the gem'
    )
    version = serializers.CharField(
        help_text='Version of the gem'
    )

    class Meta:
        fields = tuple(set(platform.ContentSerializer.Meta.fields) - {'artifacts'}) + ('name',
                                                                                       'version')
        model = models.GemContent


class GemRemoteSerializer(platform.RemoteSerializer):
    """
    A Serializer for GemRemote.
    """

    class Meta:
        fields = platform.RemoteSerializer.Meta.fields
        model = models.GemRemote


class GemPublisherSerializer(platform.PublisherSerializer):
    """
    A Serializer for GemPublisher.
    """

    class Meta:
        fields = platform.PublisherSerializer.Meta.fields
        model = models.GemPublisher
