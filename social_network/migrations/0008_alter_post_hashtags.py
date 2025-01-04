# Generated by Django 5.1.4 on 2025-01-04 12:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("social_network", "0007_comment"),
    ]

    operations = [
        migrations.AlterField(
            model_name="post",
            name="hashtags",
            field=models.ManyToManyField(
                blank=True, related_name="posts", to="social_network.hashtag"
            ),
        ),
    ]
