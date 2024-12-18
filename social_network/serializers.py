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

    def update(self, instance, validated_data):
        """"
        If no new profile image in the request, keep the existing one.
        """
        if not validated_data["profile_image" ]:
            validated_data["profile_image"] = instance.profile_image
        return super().update(instance, validated_data)


class ProfileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("id", "profile_image", "username", "full_name")
