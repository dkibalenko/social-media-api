from rest_framework import serializers

from social_network.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

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
        )


class ProfileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("id", "profile_image", "username", "full_name")
