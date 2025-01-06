from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

from social_network.models import (
    Comment,
    HashTag,
    Profile,
    FollowingInteraction,
    Post,
    Like,
)


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


class ProfileListSerializer(ProfileSerializer):
    followed_by_me = serializers.SerializerMethodField()
    followers_total = serializers.IntegerField(read_only=True)
    followees_total = serializers.IntegerField(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = (
            "id",
            "profile_image",
            "username",
            "full_name",
            "followed_by_me",
            "followers_total",
            "followees_total",
        )

    def get_followed_by_me(self, obj: Profile) -> bool:
        request = self.context.get("request", None)
        if request is not None and request.user.is_authenticated:
            return obj.followed_by_me
        return False
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_full_name(self, obj: Profile) -> str:
        return obj.full_name


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


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(
        source="author.username",
        read_only=True
    )
    author_full_name = serializers.CharField(
        source="author.full_name",
        read_only=True
    )
    author_image = serializers.ImageField(
        source="author.profile_image",
        read_only=True
    )
    image = serializers.ImageField(read_only=True, required=False)
    hashtags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False
    )
    hashtags_objects = serializers.StringRelatedField(
        source="hashtags",
        many=True,
        read_only=True
    )
    scheduled_at = serializers.DateTimeField(required=False, write_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "author_username",
            "author_full_name",
            "title",
            "hashtags",
            "hashtags_objects",
            "content",
            "image",
            "author_image",
            "created_at",
            "scheduled_at",
        )

    def create(self, validated_data) -> Post:
        """
        Creates a new Post instance with the given validated data and
        adds any provided hashtag captions to the post's hashtags.
        """
        hashtags_data = validated_data.pop("hashtags", [])
        post = Post.objects.create(**validated_data)

        for caption in hashtags_data:
            hashtag, created = HashTag.objects.get_or_create(caption=caption)
            post.hashtags.add(hashtag)
        return post


class PostListSerializer(PostSerializer):
    liked_by_user = serializers.SerializerMethodField()
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "author_username",
            "title",
            "hashtags_objects",
            "created_at",
            "liked_by_user",
            "likes_count",
            "comments_count",
            "scheduled_at",
        )

    def get_liked_by_user(self, obj: Post) -> bool:
        request = self.context.get("request", None)
        if request is not None and request.user.is_authenticated:
            return obj.liked_by_user
        return False


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("id","image",)


class LikeSerializer(serializers.ModelSerializer):
    liked_by = serializers.StringRelatedField(
        source="profile.username",
        read_only=True
    )

    class Meta:
        model = Like
        fields = ("id", "liked_by")


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(
        source="author.username",
        read_only=True
    )
    commented_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Comment
        fields = (
            "id",
            "author_username",
            "content",
            "commented_at"
        )


class PostDetailSerializer(PostSerializer):
    likes = LikeSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + ("likes", "comments")
