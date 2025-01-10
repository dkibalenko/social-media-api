from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from social_network.models import Comment, Post


class CommentViewSetTests(APITestCase):
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
        self.comment = Comment.objects.create(
            author=self.user.profile,
            post=self.post,
            content="This is a test comment."
        )

    def test_list_comments_endpoint(self):
        url = reverse("social_network:post-comments-list", args=[self.post.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.comment.id)
        self.assertEqual(response.data[0]["content"], self.comment.content)

    def test_retrieve_comment_endpoint(self):
        url = reverse(
            "social_network:post-comments-detail",
            args=[self.post.pk, self.comment.pk]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.comment.id)
        self.assertEqual(response.data["content"], self.comment.content)

    def test_create_comment_endpoint(self):
        url = reverse("social_network:post-comments-list", args=[self.post.pk])
        data = {
            "content": "This is a new comment."
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["content"], data["content"])

    def test_update_comment_endpoint(self):
        url = reverse(
            "social_network:post-comments-detail",
            args=[self.post.pk, self.comment.pk]
        )
        data = {
            "content": "This is an updated comment."
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["content"], data["content"])

    def test_delete_comment_endpoint(self):
        url = reverse(
            "social_network:post-comments-detail",
            args=[self.post.pk, self.comment.pk]
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(id=self.comment.id).exists())
