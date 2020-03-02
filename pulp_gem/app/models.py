from logging import getLogger

from django.db import models

from pulpcore.plugin.models import (
    Content,
    Remote,
    Repository,
    Publication,
    PublicationDistribution,
)

logger = getLogger(__name__)


class GemContent(Content):
    """
    The "gem" content type.

    Content of this type represents a ruby gem file
    with its spec data.

    Fields:
        name (str): The name of the gem.
        version (str): The version of the gem.

    """

    TYPE = "gem"

    name = models.TextField(blank=False, null=False)
    version = models.TextField(blank=False, null=False)

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"
        unique_together = ("name", "version")


class GemPublication(Publication):
    """
    A Publication for GemContent.
    """

    TYPE = "gem"

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"


class GemRemote(Remote):
    """
    A Remote for GemContent.
    """

    TYPE = "gem"

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"


class GemRepository(Repository):
    """
    A Repository for GemContent.
    """

    TYPE = "gem"

    CONTENT_TYPES = [GemContent]

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"


class GemDistribution(PublicationDistribution):
    """
    A Distribution for GemContent.
    """

    TYPE = "gem"

    class Meta:
        default_related_name = "%(app_label)s_%(model_name)s"
