from django.conf import settings
from django.db import models

from social_network.upload_to_path import UploadToPath


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    username = models.CharField(max_length=100)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    bio = models.TextField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_image = models.ImageField(
        upload_to=UploadToPath("profile_images/"), blank=True, null=True
    )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ["first_name", "last_name"]
        verbose_name_plural = "profiles"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"


class FollowingInteraction(models.Model):
    follower = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="followees",
    )
    followee = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="followers",
    )
    followed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["follower", "followee"]

    def __str__(self):
        return f"{self.follower} follows {self.followee}"
    

class HashTag(models.Model):
    caption = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.caption}"


class Post(models.Model):
    title = models.CharField(max_length=80)
    content = models.TextField()
    image = models.ImageField(
        upload_to=UploadToPath("post_images/"),
        blank=True,
        null=True,
    )
    hashtags = models.ManyToManyField(
        to=HashTag,
        related_name="posts",
        blank=True,
    )
    author = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_at = models.DateTimeField(blank=True, null=True, default=None)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Post by {self.author} at {self.created_at}"


class Like(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    liked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["post", "profile"]

    def __str__(self):
        return f"{self.profile} liked {self.post} at {self.liked_at}"


class Comment(models.Model):
    author = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    content = models.TextField()
    commented_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["commented_at"]

    def __str__(self):
        return f"{self.author} commented on {self.post} at {self.commented_at}"
