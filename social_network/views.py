from django.db.models import Count
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework import generics
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import serializers

from social_network.models import (
    Comment,
    FollowingInteraction,
    HashTag,
    Like,
    Post,
    Profile
)
from social_network.serializers import (
    CommentSerializer,
    PostImageSerializer,
    ProfileSerializer,
    ProfileListSerializer,
    ProfileDetailSerializer,
    EmptySerializer,
    FollowerSerializer,
    FolloweeSerializer,
    PostSerializer,
)


class CurrentUserProfileView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileSerializer

    def get_object(self) -> Profile:
        return generics.get_object_or_404(self.get_queryset())

    def get_queryset(self) -> QuerySet[Profile]:
        return (
            Profile.objects.filter(user=self.request.user)
            .prefetch_related("followees", "followers")
            .annotate(
                followers_total=Count("followers"),
                followees_total=Count("followees")
            )
        )

    def destroy(self, request, *args, **kwargs) -> Response:
        profile = self.get_object()
        user = profile.user
        response = super().destroy(request, *args, **kwargs)
        user.delete()
        return response


class ProfileViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Profile.objects.all()
    serializer_class = ProfileListSerializer
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self) -> serializers.BaseSerializer:
        if self.action == "list":
            return ProfileListSerializer
        if self.action == "retrieve":
            return ProfileDetailSerializer
        if self.action == "follow" or self.action == "unfollow":
            return EmptySerializer
        return ProfileListSerializer

    def get_queryset(self) -> QuerySet[Profile]:
        """
        Returns a filtered queryset of Profile objects
        based on query parameters.
        """

        username = self.request.query_params.get("username")
        first_name = self.request.query_params.get("first_name")
        last_name = self.request.query_params.get("last_name")

        queryset = super().get_queryset()

        if username:
            queryset = queryset.filter(username__icontains=username)

        if first_name:
            queryset = queryset.filter(first_name__icontains=first_name)

        if last_name:
            queryset = queryset.filter(last_name__icontains=last_name)

        return queryset.distinct()

    def get_current_user_profile(self) -> Profile:
        return get_object_or_404(Profile, user=self.request.user)

    @action(
        detail=True,
        methods=["post"],
        url_path="follow",
        permission_classes=[IsAuthenticated]
    )
    def follow(self, request, pk: int) -> Response:
        follower = self.get_current_user_profile()
        followee = get_object_or_404(Profile, pk=pk)

        if follower == followee:
            return Response(
                {"detail": "You cannot follow yourself."},
                status=status.HTTP_409_CONFLICT,
            )

        if follower.followees.filter(followee=followee).exists():
            return Response(
                {"detail": "You are already following this user."},
                status=status.HTTP_409_CONFLICT,
            )

        FollowingInteraction.objects.create(
            follower=follower,
            followee=followee
        )

        return Response(
            {"detail": "You are now following this user."},
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="unfollow",
        permission_classes=[IsAuthenticated]
    )
    def unfollow(self, request, pk: int) -> Response:
        follower = self.get_current_user_profile()
        followee = get_object_or_404(Profile, pk=pk)

        if follower == followee:
            return Response(
                {"detail": "You cannot unfollow yourself."},
                status=status.HTTP_409_CONFLICT,
            )

        if not follower.followees.filter(followee=followee).exists():
            return Response(
                {"detail": "You are not following this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        follower.followees.filter(followee=followee).delete()

        return Response(
            {"detail": "You are no longer following this user."},
            status=status.HTTP_200_OK
        )


class CurrentUserProfileFollowersView(generics.ListAPIView):
    serializer_class = FollowerSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self) -> QuerySet[FollowingInteraction]:
        user = self.request.user
        return user.profile.followers.all()


class CurrentUserProfileFolloweesView(generics.ListAPIView):
    serializer_class = FolloweeSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self) -> QuerySet[FollowingInteraction]:
        user = self.request.user
        return user.profile.followees.all()


class PostViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = PostSerializer
    queryset = Post.objects.all()

    def get_queryset(self) -> QuerySet[Post]:
        """
        Returns a filtered queryset of Post objects based on query parameters.

        Query parameters that can be used to filter the queryset are:

        - `hashtag`: The caption of a hashtag to filter by.
        - `author_username`: The username of the author to filter by.

        The filtering is case-insensitive.
        """
        queryset = super().get_queryset()
        hashtag = self.request.query_params.get("hashtag")
        author_username = self.request.query_params.get("author_username")

        if hashtag:
            queryset = queryset.filter(hashtags__caption__iexact=hashtag)

        if author_username:
            queryset = queryset.filter(
                author__username__icontains=author_username
            )

        return queryset

    def get_serializer_class(self) -> serializers.BaseSerializer:
        if self.action == "list":
            return PostSerializer
        if self.action == "upload_image":
            return PostImageSerializer
        if self.action in ["like", "unlike"]:
            return EmptySerializer
        return PostSerializer

    def perform_create(self, serializer: PostSerializer) -> None:
        """
        Saves the post instance with the current user's profile as the author,
        and associates any provided hashtags with the post.

        Args:
            serializer: The serializer containing the validated data
                for the post to be created.
        """
        hashtag_data = serializer.validated_data.pop("hashtags", [])
        post = serializer.save(author=self.request.user.profile)

        for caption in hashtag_data:
            hashtag, created = HashTag.objects.get_or_create(caption=caption)
            post.hashtags.add(hashtag)

    @action(
        detail=True,
        methods=["post"],
        url_path="upload-image",
    )
    def upload_image(self, request, pk: int=None) -> Response:
        post = get_object_or_404(Post, pk=pk)
        post.image = request.data["image"]
        post.save()
        return Response(
            {"detail": "Image uploaded successfully."},
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="my-posts",
    )
    def my_posts(self, request) -> Response:
        queryset = Post.objects.filter(author=request.user.profile)
        serializer = PostSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="followees-posts",
    )
    def followees_posts(self, request) -> Response:
        user_profile = request.user.profile
        followees_profiles = user_profile.followees.values_list(
            "followee",
            flat=True
        )
        followees_posts = Post.objects.filter(author__in=followees_profiles)
        serializer = PostSerializer(followees_posts, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        url_path="like",
    )
    def like(self, request, pk: int) -> Response:
        post = get_object_or_404(Post, pk=pk)
        user_profile = request.user.profile

        if Like.objects.filter(post=post, profile=user_profile).exists():
            return Response(
                {"detail": "You have already liked this post."},
                status=status.HTTP_409_CONFLICT,
            )

        Like.objects.create(post=post, profile=user_profile)
        return Response(
            {"detail": "You have liked this post."},
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="unlike",
    )
    def unlike(self, request, pk: int) -> Response:
        post = get_object_or_404(Post, pk=pk)
        user_profile = request.user.profile

        if not Like.objects.filter(post=post, profile=user_profile).exists():
            return Response(
                {"detail": "You have not liked this post."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        Like.objects.filter(post=post, profile=user_profile).delete()
        return Response(
            {"detail": "You have unliked this post."},
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="liked",
    )
    def liked(self, request) -> Response:
        user_profile = request.user.profile
        liked_posts = self.get_queryset().filter(likes__profile=user_profile)
        serialzer = PostSerializer(liked_posts, many=True)
        return Response(serialzer.data)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self) -> QuerySet:
        queryset = Comment.objects.filter(
            post_id=self.kwargs["post_pk"]
        )
        return queryset
    
    def perform_create(self, serializer: CommentSerializer) -> None:
        post = get_object_or_404(Post, pk=self.kwargs.get("post_pk"))
        serializer.save(author=self.request.user.profile, post=post)
