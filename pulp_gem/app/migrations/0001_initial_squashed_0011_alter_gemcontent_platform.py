# Generated by Django 4.2.16 on 2024-12-06 13:29

import django.contrib.postgres.fields.hstore
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [
        ("gem", "0001_initial"),
        ("gem", "0002_gemrepository"),
        ("gem", "0003_move_data_to_new_master_distribution_model"),
        ("gem", "0004_alter_gemcontent_content_ptr_and_more"),
        ("gem", "0005_rename_gemcontent_shallowgemcontent"),
        ("gem", "0006_gemremote_excludes_gemremote_includes_and_more"),
        ("gem", "0007_DATA_fix_prerelease"),
        ("gem", "0008_gemcontent_platform"),
        ("gem", "0009_check_datarepair"),
        ("gem", "0010_delete_shallowgemcontent"),
        ("gem", "0011_alter_gemcontent_platform"),
    ]

    dependencies = [
        ("core", "0106_alter_artifactdistribution_distribution_ptr_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="GemDistribution",
            fields=[
                (
                    "distribution_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="core.distribution",
                    ),
                ),
            ],
            options={
                "default_related_name": "%(app_label)s_%(model_name)s",
            },
            bases=("core.distribution",),
        ),
        migrations.CreateModel(
            name="GemRemote",
            fields=[
                (
                    "remote_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="core.remote",
                    ),
                ),
                ("excludes", django.contrib.postgres.fields.hstore.HStoreField(null=True)),
                ("includes", django.contrib.postgres.fields.hstore.HStoreField(null=True)),
                ("prereleases", models.BooleanField(default=False)),
            ],
            options={
                "default_related_name": "%(app_label)s_%(model_name)s",
            },
            bases=("core.remote",),
        ),
        migrations.CreateModel(
            name="GemPublication",
            fields=[
                (
                    "publication_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="core.publication",
                    ),
                ),
            ],
            options={
                "default_related_name": "%(app_label)s_%(model_name)s",
            },
            bases=("core.publication",),
        ),
        migrations.CreateModel(
            name="GemContent",
            fields=[
                (
                    "content_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="core.content",
                    ),
                ),
                ("name", models.TextField()),
                ("version", models.TextField()),
                ("checksum", models.CharField(db_index=True, max_length=64)),
                ("dependencies", django.contrib.postgres.fields.hstore.HStoreField(default=dict)),
                ("required_ruby_version", models.TextField(null=True)),
                ("required_rubygems_version", models.TextField(null=True)),
                ("prerelease", models.BooleanField(default=False)),
                ("platform", models.TextField()),
            ],
            options={
                "default_related_name": "%(app_label)s_%(model_name)s",
                "unique_together": {("checksum",)},
            },
            bases=("core.content",),
        ),
        migrations.CreateModel(
            name="GemRepository",
            fields=[
                (
                    "repository_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="core.repository",
                    ),
                ),
            ],
            options={
                "default_related_name": "%(app_label)s_%(model_name)s",
            },
            bases=("core.repository",),
        ),
    ]