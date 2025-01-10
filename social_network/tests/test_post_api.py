from datetime import datetime, timedelta
from unittest.mock import patch
import zoneinfo

from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from social_network.models import FollowingInteraction, Post, HashTag, Like


class PostViewSetTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="testpassword",
            first_name="John",
            last_name="Doe",
        )
        self.token = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.token.access_token}"
        )
        self.post = Post.objects.create(
            title="Test Post",
            content="This is a test post.",
            author=self.user.profile,
        )
        self.user_2 = get_user_model().objects.create_user(
            email="test2@test.com",
            password="testpassword2",
            first_name="Jane",
            last_name="Doe",
        )
        self.post_2 = Post.objects.create(
            title="Test Post 2",
            content="This is a test post 2.",
            author=self.user_2.profile,
        )
        
    def test_get_list_posts_endpoint(self):
        url = reverse("social_network:posts-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["id"], self.post_2.id)
        self.assertEqual(response.data[0]["title"], self.post_2.title)
        self.assertEqual(response.data[1]["id"], self.post.id)
        self.assertEqual(response.data[1]["title"], self.post.title)

    def test_get_list_posts_endpoint_filtered_by_hashtags(self):
        self.post.hashtags.add(HashTag.objects.create(caption="test"))
        self.post_2.hashtags.add(HashTag.objects.create(caption="django"))

        url = reverse("social_network:posts-list")
        response = self.client.get(url, data={"hashtags": "test"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.post.id)
        self.assertEqual(response.data[0]["title"], self.post.title)

    def test_get_list_posts_endpoint_filtered_by_author_username(self):
        self.post.author.username = "testuser"
        self.post.author.save()
        url = reverse("social_network:posts-list")
        response = self.client.get(url, data={"author_username": "testuser"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.post.id)
        self.assertEqual(response.data[0]["title"], self.post.title)

    def test_retrieve_post_endpoint(self):
        url = reverse(
            "social_network:posts-detail",
            args=[self.post.pk]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.post.id)
        self.assertEqual(response.data["title"], self.post.title)

    def test_create_post_endpoint(self):
        url = reverse("social_network:posts-list")
        data = {
            "title": "New Post",
            "content": "This is a new post.",
            "hashtags": ["test", "django"]
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], data["title"])
        self.assertEqual(response.data["content"], data["content"])
        self.assertEqual(len(response.data["hashtags_objects"]), 2)
    
    def test_upload_image_endpoint(self):
        url = reverse(
            "social_network:posts-upload-image",
            args=[self.post.pk]
        )
        data = {"image": "test_image.jpg"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"],
            "Image uploaded successfully."
        )

    def test_my_posts_endpoint(self):
        url = reverse("social_network:posts-my-posts")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.post.id)
        self.assertEqual(response.data[0]["title"], self.post.title)

    def test_followees_posts_endpoint(self):
        FollowingInteraction.objects.create(
            follower=self.user.profile,
            followee=self.user_2.profile
        )
        url = reverse("social_network:posts-followees-posts")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.post_2.id)
        self.assertEqual(response.data[0]["title"], self.post_2.title)

    def test_like_post_endpoint(self):
        url = reverse(
            "social_network:posts-like",
            args=[self.post.pk]
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.post.likes.count(), 1)
        self.assertEqual(self.post_2.likes.count(), 0)

        url = reverse(
            "social_network:posts-like",
            args=[self.post.pk]
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(self.post.likes.count(), 1)
        self.assertEqual(self.post_2.likes.count(), 0)

    def test_unlike_post_endpoint(self):
        Like.objects.create(post=self.post, profile=self.user.profile)
        url = reverse(
            "social_network:posts-unlike",
            args=[self.post.pk]
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.post.likes.count(), 0)
        self.assertEqual(self.post_2.likes.count(), 0)

        url = reverse(
            "social_network:posts-unlike",
            args=[self.post.pk]
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.post.likes.count(), 0)
        self.assertEqual(self.post_2.likes.count(), 0)

    def test_liked_posts_endpoint(self):
        Like.objects.create(post=self.post, profile=self.user.profile)
        url = reverse("social_network:posts-liked")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.post.id)
        self.assertEqual(response.data[0]["title"], self.post.title)
    
    @patch("social_network.views.create_scheduled_post.apply_async")
    def test_schedule_post(self, mock_apply_async):
        scheduled_time = datetime.now() + timedelta(days=1)
        data = {
            "title": "Scheduled Post",
            "content": "This is a scheduled post.",
            "hashtags": ["test", "django"],
            "scheduled_at": scheduled_time.isoformat()
        }
        url = reverse("social_network:posts-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        cet = zoneinfo.ZoneInfo("Europe/Prague")
        scheduled_time_cet = scheduled_time.replace(tzinfo=cet)

        post_data = {
            "title": data["title"],
            "content": data["content"],
            "author_id": self.user.profile.pk,
            "hashtags": data["hashtags"],
            "image": None,
        }

        mock_apply_async.assert_called_once_with(
            eta=scheduled_time_cet,
            kwargs={"post_data": post_data}
        )
