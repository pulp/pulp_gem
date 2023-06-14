from gettext import gettext as _

from django.core.management import BaseCommand

from pulpcore.plugin.util import get_url
from pulpcore.plugin.models import RepositoryContent
from pulp_gem.app.models import ShallowGemContent
from pulp_gem.app.serializers import GemContentSerializer


def replace_content(old_content, new_content):
    """Exchange all occurances of `old_content` in repository versions with `new_content`."""
    RepositoryContent.objects.filter(content_id=old_content.pk).update(content_id=new_content.pk)


class Command(BaseCommand):
    """
    Django management command for migrating shallow gems.
    """

    help = "This script migrates the pre GA generated gem content if artifacts are available."

    def add_arguments(self, parser):
        """Set up arguments."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help=_("Don't modify anything, just collect results."),
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        failed_gems = 0
        migrated_gems = 0

        shallow_gem_qs = ShallowGemContent.objects.all()
        count = shallow_gem_qs.count()
        print(f"Shallow Gems count: {count}")
        if count == 0:
            return

        for sgem in shallow_gem_qs:
            try:
                artifact = sgem.contentartifact_set.get(relative_path=sgem.relative_path).artifact
                serializer = GemContentSerializer(data={"artifact": get_url(artifact)})
                serializer.is_valid(raise_exception=True)
                assert serializer.validated_data["name"] == sgem.name
                assert serializer.validated_data["version"] == sgem.version
                if not dry_run:
                    gem = serializer.create(serializer.validated_data)
                    replace_content(sgem, gem)
                    sgem.delete()
            except Exception as e:
                failed_gems += 1
                print(f"Failed to migrate gem '{sgem.name}' '{sgem.version}': {e}")
            else:
                migrated_gems += 1

        print(f"Successfully migrated gems: {migrated_gems}")
        print(f"Gems failed to migrate: {failed_gems}")
