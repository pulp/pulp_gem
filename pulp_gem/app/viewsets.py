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
    RolesMixin,
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

    DEFAULT_ACCESS_POLICY = {
        "statements": [
            {
                "action": ["list", "retrieve"],
                "principal": "authenticated",
                "effect": "allow",
            },
            {
                "action": ["create"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": [
                    "has_required_repo_perms_on_upload:gem.modify_gemrepository",
                    "has_upload_param_model_or_domain_or_obj_perms:core.change_upload",
                ],
            },
        ],
        "queryset_scoping": {"function": "scope_queryset"},
    }


class GemRemoteViewSet(RemoteViewSet, RolesMixin):
    """
    A ViewSet for GemRemote.
    """

    endpoint_name = "gem"
    queryset = GemRemote.objects.all()
    serializer_class = GemRemoteSerializer
    queryset_filtering_required_permission = "gem.view_gemremote"

    DEFAULT_ACCESS_POLICY = {
        "statements": [
            {
                "action": ["list", "my_permissions"],
                "principal": "authenticated",
                "effect": "allow",
            },
            {
                "action": ["create"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": "has_model_or_domain_perms:gem.add_gemremote",
            },
            {
                "action": ["retrieve"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": "has_model_or_domain_or_obj_perms:gem.view_gemremote",
            },
            {
                "action": ["update", "partial_update", "set_label", "unset_label"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": [
                    "has_model_or_domain_or_obj_perms:gem.change_gemremote",
                ],
            },
            {
                "action": ["destroy"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": [
                    "has_model_or_domain_or_obj_perms:gem.delete_gemremote",
                ],
            },
            {
                "action": ["list_roles", "add_role", "remove_role"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": ["has_model_or_domain_or_obj_perms:gem.manage_roles_gemremote"],
            },
        ],
        "creation_hooks": [
            {
                "function": "add_roles_for_object_creator",
                "parameters": {"roles": "gem.gemremote_owner"},
            },
        ],
        "queryset_scoping": {"function": "scope_queryset"},
    }
    LOCKED_ROLES = {
        "gem.gemremote_creator": ["gem.add_gemremote"],
        "gem.gemremote_owner": [
            "gem.view_gemremote",
            "gem.change_gemremote",
            "gem.delete_gemremote",
            "gem.manage_roles_gemremote",
        ],
        "gem.gemremote_viewer": ["gem.view_gemremote"],
    }


class GemPublicationViewSet(PublicationViewSet, RolesMixin):
    """
    A ViewSet for GemPublication.
    """

    endpoint_name = "gem"
    queryset = GemPublication.objects.exclude(complete=False)
    serializer_class = GemPublicationSerializer
    queryset_filtering_required_permission = "gem.view_gempublication"

    DEFAULT_ACCESS_POLICY = {
        "statements": [
            {
                "action": ["list", "my_permissions"],
                "principal": "authenticated",
                "effect": "allow",
            },
            {
                "action": ["create"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": [
                    "has_model_or_domain_perms:gem.add_gempublication",
                    "has_repo_or_repo_ver_param_model_or_domain_or_obj_perms:"
                    "gem.view_gemrepository",
                ],
            },
            {
                "action": ["retrieve"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": "has_model_or_domain_or_obj_perms:gem.view_gempublication",
            },
            {
                "action": ["destroy"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": [
                    "has_model_or_domain_or_obj_perms:gem.delete_gempublication",
                ],
            },
            {
                "action": ["list_roles", "add_role", "remove_role"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": ["has_model_or_domain_or_obj_perms:gem.manage_roles_gempublication"],
            },
        ],
        "creation_hooks": [
            {
                "function": "add_roles_for_object_creator",
                "parameters": {"roles": "gem.gempublication_owner"},
            },
        ],
        "queryset_scoping": {"function": "scope_queryset"},
    }
    LOCKED_ROLES = {
        "gem.gempublication_creator": ["gem.add_gempublication"],
        "gem.gempublication_owner": [
            "gem.view_gempublication",
            "gem.delete_gempublication",
            "gem.manage_roles_gempublication",
        ],
        "gem.gempublication_viewer": ["gem.view_gempublication"],
    }

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


class GemRepositoryViewSet(RepositoryViewSet, ModifyRepositoryActionMixin, RolesMixin):
    """
    A ViewSet for GemRepository.
    """

    endpoint_name = "gem"
    queryset = GemRepository.objects.all()
    serializer_class = GemRepositorySerializer
    queryset_filtering_required_permission = "gem.view_gemrepository"

    DEFAULT_ACCESS_POLICY = {
        "statements": [
            {
                "action": ["list", "my_permissions"],
                "principal": "authenticated",
                "effect": "allow",
            },
            {
                "action": ["create"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": [
                    "has_model_or_domain_perms:gem.add_gemrepository",
                    "has_remote_param_model_or_domain_or_obj_perms:gem.view_gemremote",
                ],
            },
            {
                "action": ["retrieve"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": "has_model_or_domain_or_obj_perms:gem.view_gemrepository",
            },
            {
                "action": ["destroy"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": [
                    "has_model_or_domain_or_obj_perms:gem.delete_gemrepository",
                ],
            },
            {
                "action": ["update", "partial_update", "set_label", "unset_label"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": [
                    "has_model_or_domain_or_obj_perms:gem.change_gemrepository",
                    "has_remote_param_model_or_domain_or_obj_perms:gem.view_gemremote",
                ],
            },
            {
                "action": ["sync"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": [
                    "has_model_or_domain_or_obj_perms:gem.sync_gemrepository",
                    "has_remote_param_model_or_domain_or_obj_perms:gem.view_gemremote",
                ],
            },
            {
                "action": ["modify"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": [
                    "has_model_or_domain_or_obj_perms:gem.modify_gemrepository",
                ],
            },
            {
                "action": ["list_roles", "add_role", "remove_role"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": ["has_model_or_domain_or_obj_perms:gem.manage_roles_gemrepository"],
            },
        ],
        "creation_hooks": [
            {
                "function": "add_roles_for_object_creator",
                "parameters": {"roles": "gem.gemrepository_owner"},
            },
        ],
        "queryset_scoping": {"function": "scope_queryset"},
    }
    LOCKED_ROLES = {
        "gem.gemrepository_creator": ["gem.add_gemrepository"],
        "gem.gemrepository_owner": [
            "gem.view_gemrepository",
            "gem.change_gemrepository",
            "gem.delete_gemrepository",
            "gem.modify_gemrepository",
            "gem.sync_gemrepository",
            "gem.manage_roles_gemrepository",
            "gem.repair_gemrepository",
        ],
        "gem.gemrepository_viewer": ["gem.view_gemrepository"],
    }

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

    DEFAULT_ACCESS_POLICY = {
        "statements": [
            {
                "action": ["list", "retrieve"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": "has_repository_model_or_domain_or_obj_perms:gem.view_gemrepository",
            },
            {
                "action": ["destroy"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": [
                    "has_repository_model_or_domain_or_obj_perms:gem.delete_gemrepository",
                ],
            },
            {
                "action": ["repair"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": [
                    "has_repository_model_or_domain_or_obj_perms:gem.repair_gemrepository",
                ],
            },
        ],
    }


class GemDistributionViewSet(DistributionViewSet, RolesMixin):
    """
    ViewSet for GemDistributions.
    """

    endpoint_name = "gem"
    queryset = GemDistribution.objects.all()
    serializer_class = GemDistributionSerializer
    queryset_filtering_required_permission = "gem.view_gemdistribution"

    DEFAULT_ACCESS_POLICY = {
        "statements": [
            {
                "action": ["list", "my_permissions"],
                "principal": "authenticated",
                "effect": "allow",
            },
            {
                "action": ["create"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": [
                    "has_model_or_domain_perms:gem.add_gemdistribution",
                    "has_repo_or_repo_ver_param_model_or_domain_or_obj_perms:"
                    "gem.view_gemrepository",
                    "has_publication_param_model_or_domain_or_obj_perms:gem.view_gempublication",
                ],
            },
            {
                "action": ["retrieve"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": "has_model_or_domain_or_obj_perms:gem.view_gemdistribution",
            },
            {
                "action": ["update", "partial_update", "set_label", "unset_label"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": [
                    "has_model_or_domain_or_obj_perms:gem.change_gemdistribution",
                    "has_repo_or_repo_ver_param_model_or_domain_or_obj_perms:"
                    "gem.view_gemrepository",
                    "has_publication_param_model_or_domain_or_obj_perms:gem.view_gempublication",
                ],
            },
            {
                "action": ["destroy"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": [
                    "has_model_or_domain_or_obj_perms:gem.delete_gemdistribution",
                ],
            },
            {
                "action": ["list_roles", "add_role", "remove_role"],
                "principal": "authenticated",
                "effect": "allow",
                "condition": ["has_model_or_domain_or_obj_perms:gem.manage_roles_gemdistribution"],
            },
        ],
        "creation_hooks": [
            {
                "function": "add_roles_for_object_creator",
                "parameters": {"roles": "gem.gemdistribution_owner"},
            },
        ],
        "queryset_scoping": {"function": "scope_queryset"},
    }
    LOCKED_ROLES = {
        "gem.gemdistribution_creator": ["gem.add_gemdistribution"],
        "gem.gemdistribution_owner": [
            "gem.view_gemdistribution",
            "gem.change_gemdistribution",
            "gem.delete_gemdistribution",
            "gem.manage_roles_gemdistribution",
        ],
        "gem.gemdistribution_viewer": ["gem.view_gemdistribution"],
    }
