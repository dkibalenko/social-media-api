from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from social_network.models import Profile, FollowingInteraction


class ProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    followers_total = serializers.IntegerField(read_only=True)
    followees_total = serializers.IntegerField(read_only=True)

    class Meta:
        model = Profile
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "profile_image",
            "user_email",
            "birth_date",
            "phone_number",
            "bio",
            "followers_total",
            "followees_total",
        )

    def update(self, instance, validated_data):
        """"
        If no new profile image in the request, keep the existing one.
        """
        if not validated_data["profile_image" ]:
            validated_data["profile_image"] = instance.profile_image
        return super().update(instance, validated_data)


class ProfileListSerializer(serializers.ModelSerializer):
    followed_by_me = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = (
            "id",
            "profile_image",
            "username",
            "full_name",
            "followed_by_me"
        )

    def get_followed_by_me(self, obj):
        """
        Determines if the current user follows the given profile.

        Args:
            obj (Profile): The profile object to check against.

        Returns:
            bool: True if the current user follows the profile, False otherwise.
        """

        request = self.context.get("request", None)
        if request is not None:
            user_profile = get_object_or_404(Profile, user=request.user)
            return obj.followers.filter(follower=user_profile).exists()
        return False


class FollowerSerializer(serializers.ModelSerializer):
    profile_id = serializers.IntegerField(source="follower.id", read_only=True)
    username = serializers.CharField(source="follower.username")

    class Meta:
        model = FollowingInteraction
        fields = ("profile_id", "username")


class FolloweeSerializer(serializers.ModelSerializer):
    profile_id = serializers.IntegerField(source="followee.id", read_only=True)
    username = serializers.CharField(source="followee.username")

    class Meta:
        model = FollowingInteraction
        fields = ("profile_id", "username")


class ProfileDetailSerializer(ProfileSerializer):
    followers = FollowerSerializer(many=True, read_only=True)
    followees = FolloweeSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "profile_image",
            "user_email",
            "birth_date",
            "phone_number",
            "bio",
            "followers",
            "followees",
        )

class EmptySerializer(serializers.Serializer):
    pass
