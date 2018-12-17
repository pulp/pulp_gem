from logging import getLogger

from django.db import models

from pulpcore.plugin.models import Content, Remote, Publisher


log = getLogger(__name__)


class GemContent(Content):
    """
    The "gem" content type.

    Content of this type represents a ruby gem file
    with its spec data.

    Fields:
        name (str): The name of the gem.
        version (str): The version of the gem.

    """

    TYPE = 'gem'

    name = models.TextField(blank=False, null=False)
    version = models.TextField(blank=False, null=False)

    class Meta:
        unique_together = (
            'name',
            'version'
        )


class GemPublisher(Publisher):
    """
    A Publisher for GemContent.
    """

    TYPE = 'gem'


class GemRemote(Remote):
    """
    A Remote for GemContent.
    """

    TYPE = 'gem'
