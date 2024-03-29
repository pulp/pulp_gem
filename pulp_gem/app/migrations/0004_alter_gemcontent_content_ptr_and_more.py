# Generated by Django 4.2.1 on 2023-05-15 20:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0106_alter_artifactdistribution_distribution_ptr_and_more'),
        ('gem', '0003_move_data_to_new_master_distribution_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gemcontent',
            name='content_ptr',
            field=models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.content'),
        ),
        migrations.AlterField(
            model_name='gemdistribution',
            name='distribution_ptr',
            field=models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.distribution'),
        ),
        migrations.AlterField(
            model_name='gempublication',
            name='publication_ptr',
            field=models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.publication'),
        ),
        migrations.AlterField(
            model_name='gemremote',
            name='remote_ptr',
            field=models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.remote'),
        ),
        migrations.AlterField(
            model_name='gemrepository',
            name='repository_ptr',
            field=models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.repository'),
        ),
    ]
