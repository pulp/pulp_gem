from gettext import gettext as _

import os

from rest_framework.serializers import (
    CharField,
    ChoiceField,
    FileField,
    HyperlinkedRelatedField,
    ValidationError,
)

from pulpcore.plugin.files import PulpTemporaryUploadedFile
from pulpcore.plugin.models import Artifact, Remote, Repository, RepositoryVersion
from pulpcore.plugin.serializers import (
    ArtifactSerializer,
    MultipleArtifactContentSerializer,
    PublicationSerializer,
    PublicationDistributionSerializer,
    RemoteSerializer,
    RepositorySerializer,
    SingleContentArtifactField,
)

from pulp_gem.app.models import (
    GemContent,
    GemDistribution,
    GemPublication,
    GemRemote,
    GemRepository,
)

from pulp_gem.specs import analyse_gem


def _artifact_from_data(raw_data):
    tmpfile = PulpTemporaryUploadedFile(
        "tmpfile", "application/octet-stream", len(raw_data), "", ""
    )
    tmpfile.write(raw_data)

    artifact_serializer = ArtifactSerializer(data={"file": tmpfile})
    artifact_serializer.is_valid(raise_exception=True)

    return artifact_serializer.save()


class GemContentSerializer(MultipleArtifactContentSerializer):
    """
    A Serializer for GemContent.
    """

    artifact = SingleContentArtifactField(
        help_text=_("Artifact file representing the physical content"),
        required=False,
        write_only=True,
    )
    file = FileField(
        help_text=_(
            "An uploaded file that should be turned into the artifact of the content unit."
        ),
        required=False,
        write_only=True,
    )
    repository = HyperlinkedRelatedField(
        help_text=_("A URI of a repository the new content unit should be associated with."),
        required=False,
        write_only=True,
        queryset=Repository.objects.all(),
        view_name="repositories-detail",
    )
    name = CharField(help_text=_("Name of the gem"), read_only=True)
    version = CharField(help_text=_("Version of the gem"), read_only=True)

    def __init__(self, *args, **kwargs):
        """Initializer for GemContentSerializer."""
        super().__init__(*args, **kwargs)
        self.fields["artifacts"].read_only = True

    def validate(self, data):
        """Validate the GemContent data."""
        data = super().validate(data)

        if "file" in data:
            if "artifact" in data:
                raise ValidationError(_("Only one of 'file' and 'artifact' may be specified."))
            data["artifact"] = Artifact.init_and_validate(data.pop("file"))
        elif "artifact" not in data:
            raise ValidationError(_("One of 'file' and 'artifact' must be specified."))

        if "request" not in self.context:
            data = self.deferred_validate(data)

        return data

    def deferred_validate(self, data):
        """Validate the GemContent data (deferred)."""
        artifact = data.pop("artifact")

        name, version, spec_data = analyse_gem(artifact.file)
        relative_path = os.path.join("gems", name + "-" + version + ".gem")

        spec_artifact = _artifact_from_data(spec_data)
        spec_relative_path = os.path.join("quick/Marshal.4.8", name + "-" + version + ".gemspec.rz")

        data["name"] = name
        data["version"] = version
        data["artifacts"] = {relative_path: artifact, spec_relative_path: spec_artifact}

        # Validate uniqueness
        content = GemContent.objects.filter(name=name, version=version)
        if content.exists():
            raise ValidationError(
                _(
                    "There is already a gem content with name '{name}' and version '{version}'."
                ).format(name=name, version=version)
            )

        return data

    def create(self, validated_data):
        """Save the GemContent unit.

        This must be used inside a task that locks on the Artifact and if given, the repository.
        """
        repository = validated_data.pop("repository", None)
        content = super().create(validated_data)

        if repository:
            content_to_add = self.Meta.model.objects.filter(pk=content.pk)

            # create new repo version with uploaded package
            with RepositoryVersion.create(repository) as new_version:
                new_version.add_content(content_to_add)
        return content

    class Meta:
        fields = MultipleArtifactContentSerializer.Meta.fields + (
            "artifact",
            "file",
            "repository",
            "name",
            "version",
        )
        model = GemContent


class GemRemoteSerializer(RemoteSerializer):
    """
    A Serializer for GemRemote.
    """

    policy = ChoiceField(
        help_text="The policy to use when downloading content. The possible values include: "
        "'immediate', 'on_demand', and 'streamed'. 'immediate' is the default.",
        choices=Remote.POLICY_CHOICES,
        default=Remote.IMMEDIATE,
    )

    class Meta:
        fields = RemoteSerializer.Meta.fields
        model = GemRemote


class GemRepositorySerializer(RepositorySerializer):
    """
    A Serializer for GemRepository.
    """

    class Meta:
        fields = RepositorySerializer.Meta.fields
        model = GemRepository


class GemPublicationSerializer(PublicationSerializer):
    """
    A Serializer for GemPublication.
    """

    class Meta:
        fields = PublicationSerializer.Meta.fields
        model = GemPublication


class GemDistributionSerializer(PublicationDistributionSerializer):
    """
    A Serializer for GemDistribution.
    """

    class Meta:
        fields = PublicationDistributionSerializer.Meta.fields
        model = GemDistribution
