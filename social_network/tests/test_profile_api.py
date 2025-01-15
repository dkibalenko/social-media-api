from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from social_network.models import FollowingInteraction
from social_network.serializers import EmptySerializer
from social_network.views import ProfileViewSet


CURRENT_USER_URL = reverse("social_network:me")
PROFILES_LIST_URL = reverse("social_network:profiles-list")


def sample_user_profile(**params):
    defaults = {
        "email": "test@test.com",
        "password": "testpassword",
        "first_name": "Test_first_name",
        "last_name": "Test_last_name",
    }
    defaults.update(params)
    return get_user_model().objects.create_user(**defaults)


class CurrentUserProfileViewTests(APITestCase):
    def setUp(self):
        self.user = sample_user_profile(
            email="test@test.com",
            password="testpassword",
            first_name="John",
            last_name="Doe",
        )
        self.token = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.token.access_token}"
        )
        self.user_2 = sample_user_profile(
            email="test2@test.com",
            password="testpassword2",
            first_name="Jane",
            last_name="Doe",
        )

    def test_get_profile(self):
        response = self.client.get(CURRENT_USER_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["first_name"],
            self.user.profile.first_name
        )
        self.assertEqual(
            response.data["last_name"],
            self.user.profile.last_name
        )

    def test_update_profile(self):
        data = {
            "username": "johnny_updated",
            "first_name": "John",
            "last_name": "Doe",
            "birth_date": "1990-01-01",
            "phone_number": "+1234567890",
            "bio": "Hello, I am John Doe Updated!",
        }
        response = self.client.put(CURRENT_USER_URL, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "johnny_updated")
        self.assertEqual(response.data["bio"], "Hello, I am John Doe Updated!")

    def test_delete_profile(self):
        response = self.client.delete(CURRENT_USER_URL)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        user_exists = get_user_model().objects.filter(id=self.user.id).exists()
        self.assertFalse(user_exists)

    def test_get_current_user_followers(self):
        FollowingInteraction.objects.create(
            follower=self.user_2.profile,
            followee=self.user.profile
        )
        url = reverse("social_network:me-followers")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["profile_id"],
            self.user_2.profile.pk
        )

    def test_get_current_user_followees(self):
        FollowingInteraction.objects.create(
            follower=self.user.profile, followee=self.user_2.profile
        )
        url = reverse("social_network:me-followees")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["profile_id"],
            self.user_2.profile.pk
        )


class ProfileViewSetTests(APITestCase):
    def setUp(self):
        self.user = sample_user_profile(
            email="test@test.com",
            password="testpassword",
            first_name="John",
            last_name="Doe",
        )
        self.token = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.token.access_token}"
        )
        self.user_2 = sample_user_profile(
            email="test2@test.com",
            password="testpassword2",
            first_name="Jane",
            last_name="Doe",
        )

    def test_get_profile_list_endpoint(self):
        response = self.client.get(PROFILES_LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["id"], self.user.profile.pk)
        self.assertEqual(response.data[1]["id"], self.user_2.profile.pk)

    def test_retrieve_profile_endpoint(self):
        url = reverse(
            "social_network:profiles-detail",
            args=[self.user.profile.pk]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.user.profile.id)

    def test_follow_profile_endpoint(self):
        url = reverse(
            "social_network:profiles-follow",
            args=[self.user_2.profile.pk]
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.user.profile.followees.count(), 1)
        self.assertEqual(self.user_2.profile.followers.count(), 1)

    def test_follow_profile_endpoint_twice(self):
        url = reverse(
            "social_network:profiles-follow",
            args=[self.user_2.profile.pk]
        )
        self.client.post(url)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(self.user.profile.followees.count(), 1)
        self.assertEqual(self.user_2.profile.followers.count(), 1)

    def test_follow_self_endpoint(self):
        url = reverse(
            "social_network:profiles-follow",
            args=[self.user.profile.pk]
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(self.user.profile.followees.count(), 0)
        self.assertEqual(self.user.profile.followers.count(), 0)

    def test_follow_already_followed_endpoint(self):
        FollowingInteraction.objects.create(
            follower=self.user.profile, followee=self.user_2.profile
        )
        url = reverse(
            "social_network:profiles-follow",
            args=[self.user_2.profile.pk]
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(self.user.profile.followees.count(), 1)
        self.assertEqual(self.user_2.profile.followers.count(), 1)

    def test_unfollow_profile_endpoint(self):
        FollowingInteraction.objects.create(
            follower=self.user.profile, followee=self.user_2.profile
        )
        url = reverse(
            "social_network:profiles-unfollow",
            args=[self.user_2.profile.pk]
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.profile.followees.count(), 0)
        self.assertEqual(self.user_2.profile.followers.count(), 0)

    def test_unfollow_self_endpoint(self):
        url = reverse(
            "social_network:profiles-unfollow",
            args=[self.user.profile.pk]
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(self.user.profile.followees.count(), 0)
        self.assertEqual(self.user.profile.followers.count(), 0)

    def test_unfollow_unfollowed_endpoint(self):
        url = reverse(
            "social_network:profiles-unfollow",
            args=[self.user_2.profile.pk]
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.user.profile.followees.count(), 0)
        self.assertEqual(self.user_2.profile.followers.count(), 0)

    def test_get_serializer_class_follow_unfollow(self):
        view = ProfileViewSet()
        view.action = "follow"
        serializer_class = view.get_serializer_class()
        self.assertEqual(serializer_class, EmptySerializer)

        view.action = "unfollow"
        serializer_class = view.get_serializer_class()
        self.assertEqual(serializer_class, EmptySerializer)

    def test_retrieve_profile_list_endpoint_filtered_by_username(self):
        self.user_2.profile.username = "janedoe"
        self.user_2.profile.save()
        response = self.client.get(
            PROFILES_LIST_URL,
            data={"username": "janedoe"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.user_2.profile.pk)

    def test_retrieve_profile_list_endpoint_filtered_by_first_name(self):
        self.user_2.profile.first_name = "Jane"
        self.user_2.profile.save()
        response = self.client.get(
            PROFILES_LIST_URL,
            data={"first_name": "Jane"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.user_2.profile.pk)

    def test_retrieve_profile_list_endpoint_filtered_by_last_name(self):
        self.user_2.profile.last_name = "Doe"
        self.user_2.profile.save()
        response = self.client.get(
            PROFILES_LIST_URL,
            data={"last_name": "Doe"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.user_2.profile.pk)
