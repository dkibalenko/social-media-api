# Generated by Django 5.1.4 on 2025-01-06 18:34

import django.db.models.deletion
import social_network.upload_to_path
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [
        ("social_network", "0001_initial"),
        ("social_network", "0002_followinginteraction"),
        ("social_network", "0003_alter_followinginteraction_follower"),
        ("social_network", "0004_post"),
        ("social_network", "0005_hashtag_post_title_post_hashtags"),
        ("social_network", "0006_like"),
        ("social_network", "0007_comment"),
        ("social_network", "0008_alter_post_hashtags"),
        ("social_network", "0009_post_sheduled_at"),
        ("social_network", "0010_rename_sheduled_at_post_scheduled_at"),
    ]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Profile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("username", models.CharField(max_length=100)),
                ("first_name", models.CharField(max_length=255)),
                ("last_name", models.CharField(max_length=255)),
                ("bio", models.TextField(blank=True, null=True)),
                ("birth_date", models.DateField(blank=True, null=True)),
                (
                    "phone_number",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                (
                    "profile_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=social_network.upload_to_path.UploadToPath(
                            "profile_images/"
                        ),
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "profiles",
                "ordering": ["first_name", "last_name"],
            },
        ),
        migrations.CreateModel(
            name="FollowingInteraction",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("followed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "followee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="followers",
                        to="social_network.profile",
                    ),
                ),
                (
                    "follower",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="followees",
                        to="social_network.profile",
                    ),
                ),
            ],
            options={
                "unique_together": {("follower", "followee")},
            },
        ),
        migrations.CreateModel(
            name="HashTag",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("caption", models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name="Post",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("content", models.TextField()),
                (
                    "image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=social_network.upload_to_path.UploadToPath(
                            "post_images/"
                        ),
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="posts",
                        to="social_network.profile",
                    ),
                ),
                ("title", models.CharField(default="", max_length=80)),
                (
                    "hashtags",
                    models.ManyToManyField(
                        blank=True, related_name="posts", to="social_network.hashtag"
                    ),
                ),
                (
                    "scheduled_at",
                    models.DateTimeField(blank=True, default=None, null=True),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Like",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("liked_at", models.DateTimeField(auto_now_add=True)),
                (
                    "post",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="likes",
                        to="social_network.post",
                    ),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="likes",
                        to="social_network.profile",
                    ),
                ),
            ],
            options={
                "unique_together": {("post", "profile")},
            },
        ),
        migrations.CreateModel(
            name="Comment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("content", models.TextField()),
                ("commented_at", models.DateTimeField(auto_now_add=True)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comments",
                        to="social_network.profile",
                    ),
                ),
                (
                    "post",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comments",
                        to="social_network.post",
                    ),
                ),
            ],
            options={
                "ordering": ["commented_at"],
            },
        ),
    ]