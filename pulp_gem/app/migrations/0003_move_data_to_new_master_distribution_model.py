from django.db import connection, migrations, models, transaction
import django.db.models.deletion


pks_to_delete = []


def migrate_data_from_old_master_model_to_new_master_model(apps, schema_editor):
    GemDistribution = apps.get_model("gem", "GemDistribution")
    CoreDistribution = apps.get_model("core", "Distribution")
    for old_gem_distribution in GemDistribution.objects.all():
        with transaction.atomic():
            new_master_model_entry = CoreDistribution(
                pulp_id=old_gem_distribution.pulp_id,
                pulp_created=old_gem_distribution.pulp_created,
                pulp_last_updated=old_gem_distribution.pulp_last_updated,
                pulp_type=old_gem_distribution.pulp_type,
                name=old_gem_distribution.name,
                base_path=old_gem_distribution.base_path,
                content_guard=old_gem_distribution.content_guard,
                remote=old_gem_distribution.remote,
                publication=old_gem_distribution.publication,
            )
            new_master_model_entry.save()
            old_gem_distribution.distribution_ptr = new_master_model_entry
            old_gem_distribution.save()
            pks_to_delete.append(old_gem_distribution.pulp_id)


def delete_remaining_old_master_model_entries(apps, schema_editor):
    with connection.cursor() as cursor:
        for pk in pks_to_delete:
            cursor.execute("DELETE from core_basedistribution WHERE pulp_id = %s", [pk])


class Migration(migrations.Migration):

    dependencies = [
        ("gem", "0002_gemrepository"),
    ]

    operations = [
        migrations.AddField(
            model_name="GemDistribution",
            name="distribution_ptr",
            field=models.OneToOneField(
                auto_created=True,
                null=True,
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                parent_link=True,
                primary_key=False,
                related_name="gem_gemdistribution",
                serialize=False,
                to="core.Distribution",
            ),
            preserve_default=False,
        ),
        migrations.RunPython(migrate_data_from_old_master_model_to_new_master_model, elidable=True),
        migrations.RemoveField(
            model_name="GemDistribution",
            name="basedistribution_ptr",
        ),
        migrations.AlterField(
            model_name="GemDistribution",
            name="distribution_ptr",
            field=models.OneToOneField(
                auto_created=True,
                on_delete=django.db.models.deletion.CASCADE,
                parent_link=True,
                primary_key=True,
                related_name="gem_gemdistribution",
                serialize=False,
                to="core.distribution",
            ),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name="GemDistribution",
            name="publication",
        ),
        migrations.RunPython(delete_remaining_old_master_model_entries, elidable=True),
    ]
