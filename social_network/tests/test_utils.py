import os
import uuid
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils.text import slugify
from django.contrib.auth import get_user_model

from rest_framework.test import APIRequestFactory

from social_network.models import Post
from social_network.permissions import IsOwnerOrReadOnly
from social_network.upload_to_path import UploadToPath
from social_network.tasks import create_scheduled_post
from social_network.views import PostViewSet, ProfileViewSet

class TestUploadToPath(TestCase):
    def setUp(self):
        self.upload_path = UploadToPath("uploads/")

    def test_get_directory_name(self):
        directory_name = self.upload_path.get_directory_name()
        self.assertEqual(directory_name, os.path.normpath("uploads/"))

    @patch("uuid.uuid4")
    def test_get_filename_with_name(self, mock_uuid):
        mock_uuid.return_value = "1234"
        instance = MagicMock()
        instance.first_name = "John"
        instance.last_name = "Doe"
        filename = self.upload_path.get_filename(instance, "test.jpg")
        self.assertTrue(filename.startswith("john-doe-1234"))
    
    @patch("uuid.uuid4")
    def test_get_filename_with_title(self, mock_uuid):
        mock_uuid.return_value = uuid.UUID(
            "12345678-1234-5678-1234-567812345678"
        )
        instance = MagicMock(spec="title")
        instance.title="Test Title"
        filename = self.upload_path.get_filename(instance, "test.jpg")
        expected_slug = slugify(instance.title)
        self.assertTrue(filename.startswith(f"{expected_slug}-12345678-"))
        self.assertTrue(filename.endswith(".jpg"))

    def test_generate_upload_path_with_name(self):
        instance = MagicMock(spec_set=["first_name", "last_name"])
        instance.first_name = "John"
        instance.last_name = "Doe"
        filename = self.upload_path.generate_upload_path(instance, "test.jpg")

        normalized_filename = filename.replace("\\", "/")

        self.assertTrue(normalized_filename.startswith("uploads/john-doe-"))
        self.assertTrue(filename.endswith(".jpg"))
    
    def test_generate_upload_path_with_title(self):
        instance = MagicMock(spec="title")
        instance.title = "Test Title"
        filename = self.upload_path.generate_upload_path(instance, "test.jpg")

        normalized_filename = filename.replace("\\", "/")

        self.assertTrue(normalized_filename.startswith("uploads/test-title-"))
        self.assertTrue(normalized_filename.endswith(".jpg"))

    def test_generate_upload_path_with_extension(self):
        instance = MagicMock()
        instance.first_name = "John"
        instance.last_name = "Doe"
        filename = self.upload_path.generate_upload_path(instance, "test.jpg")
        self.assertTrue(filename.endswith(".jpg"))


class CreateScheduledPostTaskTest(TestCase):
    @patch("social_network.tasks.Post")
    @patch("social_network.tasks.Profile")
    @patch("social_network.tasks.HashTag")
    def test_create_scheduled_post(
        self,
        mock_HashTag,
        mock_Profile,
        mock_Post
    ):
        post_data = {
            "title": "Test Post",
            "content": "This is a test post.",
            "author_id": 1,
            "hashtags": ["test", "django"],
            "scheduled_at": None
        }

        mock_author = MagicMock()
        mock_Profile.objects.get.return_value = mock_author

        mock_post = MagicMock()
        mock_Post.objects.create.return_value = mock_post

        mock_hashtag = MagicMock()
        mock_HashTag.objects.get_or_create.return_value = (mock_hashtag, True)

        create_scheduled_post(post_data.copy())

        mock_Profile.objects.get.assert_called_once_with(
            pk=post_data["author_id"]
        )
        mock_Post.objects.create.assert_called_once_with(
            author=mock_author,
            title=post_data["title"],
            content=post_data["content"]
        )
        for hashtag in ["test", "django"]:
            mock_HashTag.objects.get_or_create.assert_any_call(caption=hashtag)
        self.assertEqual(mock_post.hashtags.set.call_count, 1)


class TestIsOwnerOrReadOnly(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="testpassword",
            first_name="John",
            last_name="Doe",
        )
        self.user_2 = get_user_model().objects.create_user(
            email="test2@test.com",
            password="testpassword2",
            first_name="Jane",
            last_name="Doe",
        )
        self.post = Post.objects.create(
            title="Test Post",
            content="This is a test post.",
            author=self.user.profile,
        )
        self.permission = IsOwnerOrReadOnly()

    def test_has_object_permission_read_only(self):
        request = self.factory.get("/api/profiles/")
        view = MagicMock()
        obj = MagicMock(author=self.user.profile)
        self.assertTrue(
            self.permission.has_object_permission(request, view, obj)
        )

    def test_has_object_permission_profile_viewset_owner(self):
        request = self.factory.post(f"/api/profiles/{self.user.profile.pk}/")
        request.user = self.user
        view = ProfileViewSet()
        obj = self.user.profile

        self.assertTrue(
            self.permission.has_object_permission(request, view, obj)
        )

    def test_has_object_permission_profile_viewset_not_owner(self):
        request = self.factory.post(f"/api/profiles/{self.user.profile.pk}/")
        request.user = self.user_2
        view = ProfileViewSet()
        obj = self.user.profile

        self.assertFalse(
            self.permission.has_object_permission(request, view, obj)
        )

    def test_has_object_permission_post_viewset_owner(self):
        request = self.factory.put(f"/api/posts/{self.post.pk}/")
        request.user = self.user
        view = PostViewSet()
        obj = self.post

        self.assertTrue(
            self.permission.has_object_permission(request, view, obj)
        )

    def test_has_object_permission_post_viewset_not_owner(self):
        request = self.factory.put(f"/api/posts/{self.post.pk}/")
        request.user = self.user_2
        view = PostViewSet()
        obj = self.post

        self.assertFalse(
            self.permission.has_object_permission(request, view, obj)
        )
