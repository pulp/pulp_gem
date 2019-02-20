from gettext import gettext as _

import os

from rest_framework import serializers

from pulpcore.app.files import PulpTemporaryUploadedFile
from pulpcore.plugin import serializers as platform

from . import models

from ..specs import analyse_gem


def _artifact_from_data(raw_data):
    tmpfile = PulpTemporaryUploadedFile(
        "tmpfile",
        "application/octet-stream",
        len(raw_data),
        "",
        "",
    )
    tmpfile.write(raw_data)

    artifact_serializer = platform.ArtifactSerializer(data={'file': tmpfile})
    artifact_serializer.is_valid(raise_exception=True)

    return artifact_serializer.save()


class GemContentSerializer(platform.MultipleArtifactContentSerializer):
    """
    A Serializer for GemContent.
    """

    _artifact = platform.SingleContentArtifactField(
        help_text=_('Artifact file representing the physical content'),
        write_only=True,
    )
    name = serializers.CharField(
        help_text=_('Name of the gem'),
        read_only=True,
    )
    version = serializers.CharField(
        help_text=_('Version of the gem'),
        read_only=True,
    )

    def __init__(self, *args, **kwargs):
        """Initializer for GemContentSerializer."""
        super().__init__(*args, **kwargs)
        self.fields['_artifacts'].read_only = True

    def validate(self, data):
        """Validate the GemContent data."""
        data = super().validate(data)

        try:
            artifact = data.pop('_artifact')
        except KeyError:
            raise serializers.ValidationError(
                detail={'_artifact': _('This field is required')},
            )

        name, version, spec_data = analyse_gem(artifact.file.name)
        relative_path = os.path.join('gems', name + '-' + version + '.gem')

        spec_artifact = _artifact_from_data(spec_data)
        spec_relative_path = os.path.join('quick/Marshal.4.8', name + '-' + version + '.gemspec.rz')

        data['name'] = name
        data['version'] = version
        data['_artifacts'] = {
            relative_path: artifact,
            spec_relative_path: spec_artifact,
        }

        # Validate uniqueness
        content = models.GemContent.objects.filter(
            name=name,
            version=version,
        )
        if content.exists():
            raise serializers.ValidationError(_(
                "There is already a gem content with name '{name}' and version '{version}'."
            ).format(name=name, version=version))

        return data

    class Meta:
        fields = platform.MultipleArtifactContentSerializer.Meta.fields + (
            '_artifact',
            'name',
            'version',
        )
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
