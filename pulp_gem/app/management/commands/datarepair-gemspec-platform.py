from gettext import gettext as _

from django.core.management import BaseCommand
from django.db import transaction

from pulp_gem.app.models import GemContent
from pulp_gem.app.serializers import _artifact_from_data
from pulp_gem.specs import analyse_gem


class Command(BaseCommand):
    """
    Django management command to repair gems created prior to 0.2.0.
    """

    help = "This script repairs gem metadata created before 0.2.0 if artifacts are available."

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
        repaired_gems = 0

        gem_qs = GemContent.objects.filter(platform=None)
        count = gem_qs.count()
        print(f"Gems to repair: {count}")
        if count == 0:
            return

        for gem in gem_qs.iterator():
            try:
                content_artifact = gem.contentartifact_set.get(relative_path=gem.relative_path)
                artifact = content_artifact.artifact
                spec_content_artifact = gem.contentartifact_set.get(relative_path=gem.gemspec_path)
                gem_info, gemspec_data = analyse_gem(artifact.file)

                assert gem_info["name"] == gem.name
                assert gem_info["version"] == gem.version

                gem.platform = gem_info["platform"]
                content_artifact.relative_path = gem.relative_path
                spec_content_artifact.relative_path = gem.gemspec_path

                if not dry_run:
                    with transaction.atomic():
                        spec_content_artifact.artifact = _artifact_from_data(gemspec_data)
                        gem.save(update_fields=["platform"])
                        content_artifact.save(update_fields=["relative_path"])
                        spec_content_artifact.save(update_fields=["relative_path", "artifact"])
            except Exception as e:
                failed_gems += 1
                print(f"Failed to migrate gem '{gem.name}' '{gem.ext_version}': {e}")
            else:
                repaired_gems += 1

        print(f"Successfully repaired gems: {repaired_gems}")
        print(f"Gems failed to repair: {failed_gems}")
