# Generated by Django 5.1.4 on 2025-01-06 16:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("social_network", "0009_post_sheduled_at"),
    ]

    operations = [
        migrations.RenameField(
            model_name="post",
            old_name="sheduled_at",
            new_name="scheduled_at",
        ),
    ]
