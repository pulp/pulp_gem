from gettext import gettext as _
import tempfile

import hashlib
import os

from django.db import DatabaseError
from rest_framework.serializers import (
    BooleanField,
    CharField,
    ChoiceField,
    HStoreField,
)

from pulpcore.plugin.models import Artifact, Publication, Remote, Repository
from pulpcore.plugin.serializers import (
    ArtifactSerializer,
    DetailRelatedField,
    MultipleArtifactContentSerializer,
    PublicationSerializer,
    DistributionSerializer,
    RemoteSerializer,
    RepositorySerializer,
    SingleContentArtifactField,
)
from pulpcore.plugin.serializers.content import UploadSerializerFieldsMixin
from pulpcore.plugin.util import get_domain_pk

from pulp_gem.app.models import (
    GemContent,
    GemDistribution,
    GemPublication,
    GemRemote,
    GemRepository,
)

from pulp_gem.specs import analyse_gem


def _artifact_from_data(raw_data):
    sha256 = hashlib.sha256(raw_data).hexdigest()
    artifact = Artifact.objects.filter(sha256=sha256).first()
    if artifact:
        return artifact

    with tempfile.NamedTemporaryFile("wb", dir=".", delete=False) as tmpfile:
        tmpfile.write(raw_data)

    artifact = Artifact.init_and_validate(tmpfile.name, expected_digests={"sha256": sha256})
    artifact.save()
    return artifact


class GemContentSerializer(MultipleArtifactContentSerializer, UploadSerializerFieldsMixin):
    """
    A Serializer for GemContent.
    """

    artifact = SingleContentArtifactField(
        help_text=_("Artifact file representing the physical content"),
        required=False,
        write_only=True,
    )
    repository = DetailRelatedField(
        help_text=_("A URI of a repository the new content unit should be associated with."),
        required=False,
        write_only=True,
        view_name_pattern=r"repositories(-.*/.*)-detail",
        queryset=Repository.objects.all(),
    )
    checksum = CharField(help_text=_("SHA256 checksum of the gem"), read_only=True)
    name = CharField(help_text=_("Name of the gem"), read_only=True)
    version = CharField(help_text=_("Version of the gem"), read_only=True)
    platform = CharField(help_text=_("Platform of the gem"), read_only=True)
    prerelease = BooleanField(help_text=_("Whether the gem is a prerelease"), read_only=True)
    dependencies = HStoreField(read_only=True)
    required_ruby_version = CharField(
        help_text=_("Required ruby version of the gem"), read_only=True
    )
    required_rubygems_version = CharField(
        help_text=_("Required rubygems version of the gem"), read_only=True
    )

    def __init__(self, *args, **kwargs):
        """Initializer for GemContentSerializer."""
        super().__init__(*args, **kwargs)
        self.fields["artifacts"].read_only = True

    def deferred_validate(self, data):
        """Validate the GemContent data (deferred)."""
        data = super().deferred_validate(data)

        if "file" in data:
            file = data.pop("file")
            # if artifact already exists, let's use it
            try:
                artifact = Artifact.objects.get(
                    sha256=file.hashers["sha256"].hexdigest(), pulp_domain=get_domain_pk()
                )
                if not artifact.pulp_domain.get_storage().exists(artifact.file.name):
                    artifact.file = file
                    artifact.save()
                else:
                    artifact.touch()
            except (Artifact.DoesNotExist, DatabaseError):
                artifact_data = {"file": file}
                serializer = ArtifactSerializer(data=artifact_data)
                serializer.is_valid(raise_exception=True)
                artifact = serializer.save()
        else:
            artifact = data.pop("artifact")

        gem_info, spec_data = analyse_gem(artifact.file)
        relative_path = os.path.join("gems", gem_info["name"] + "-" + gem_info["version"] + ".gem")

        spec_artifact = _artifact_from_data(spec_data)
        spec_relative_path = os.path.join(
            "quick/Marshal.4.8", gem_info["name"] + "-" + gem_info["version"] + ".gemspec.rz"
        )

        data.update(gem_info)
        data["artifacts"] = {relative_path: artifact, spec_relative_path: spec_artifact}
        data["checksum"] = artifact.sha256

        return data

    def retrieve(self, validated_data):
        return GemContent.objects.filter(
            _pulp_domain=get_domain_pk(), checksum=validated_data["checksum"]
        ).first()

    class Meta:
        fields = (
            MultipleArtifactContentSerializer.Meta.fields
            + UploadSerializerFieldsMixin.Meta.fields
            + (
                "artifact",
                "repository",
                "checksum",
                "name",
                "version",
                "platform",
                "prerelease",
                "dependencies",
                "required_ruby_version",
                "required_rubygems_version",
            )
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
    prereleases = BooleanField(default=False)
    includes = HStoreField(required=False, allow_null=True)
    excludes = HStoreField(required=False, allow_null=True)

    class Meta:
        fields = RemoteSerializer.Meta.fields + ("prereleases", "includes", "excludes")
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


class GemDistributionSerializer(DistributionSerializer):
    """
    A Serializer for GemDistribution.
    """

    publication = DetailRelatedField(
        required=False,
        help_text=_("Publication to be served"),
        view_name_pattern=r"publications(-.*/.*)?-detail",
        queryset=Publication.objects.exclude(complete=False),
        allow_null=True,
    )
    remote = DetailRelatedField(
        required=False,
        help_text=_("Remote that can be used to fetch content when using pull-through caching."),
        view_name_pattern=r"remotes(-.*/.*)?-detail",
        queryset=Remote.objects.all(),
        allow_null=True,
    )

    class Meta:
        fields = DistributionSerializer.Meta.fields + ("publication", "remote")
        model = GemDistribution
