# Generated by Django 5.1.4 on 2025-01-11 17:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("social_network", "0001_squashed_0010_rename_sheduled_at_post_scheduled_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="post",
            name="title",
            field=models.CharField(max_length=80),
        ),
    ]