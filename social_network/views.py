from django.db.models import Count, Exists, OuterRef, Subquery
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
    PostDetailSerializer,
    PostImageSerializer,
    ProfileSerializer,
    ProfileListSerializer,
    ProfileDetailSerializer,
    EmptySerializer,
    FollowerSerializer,
    FolloweeSerializer,
    PostSerializer,
    PostListSerializer
)

from social_network.permissions import IsOwnerOrReadOnly


class CurrentUserProfileView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProfileSerializer

    def get_object(self) -> Profile:
        return generics.get_object_or_404(self.get_queryset())

    def get_queryset(self) -> QuerySet[Profile]:
        return (
            Profile.objects.filter(user=self.request.user)
            .select_related("user")
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
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = (IsOwnerOrReadOnly,)

    def get_serializer_class(self) -> serializers.BaseSerializer:
        if self.action == "list":
            return ProfileListSerializer
        if self.action == "retrieve":
            return ProfileDetailSerializer
        if self.action in ["follow", "unfollow"]:
            return EmptySerializer
        return ProfileListSerializer

    def get_queryset(self) -> QuerySet[Profile]:
        """
        Returns a QuerySet of Profile objects annotated with the total number
        of followers and followees each profile has, and also annotated with
        a boolean indicating whether the current user follows the profile.

        The QuerySet is filtered by the query parameters "username",
        "first_name", and "last_name", if any of them are present.

        :return: A QuerySet of Profile objects
        """
        if self.request.user.is_authenticated:
            queryset = Profile.objects.select_related(
                "user"
                ).prefetch_related(
                    "followers",
                    "followees"
                    ).annotate(
                        followed_by_me=Exists(
                            FollowingInteraction.objects.filter(
                                follower__user=self.request.user,
                                followee=OuterRef("pk")
                            )
                        ),
                        followers_total=Count("followers", distinct=True),
                        followees_total=Count("followees", distinct=True)
                    )
        else:
            queryset = Profile.objects.select_related(
                "user"
                ).prefetch_related(
                    "followers",
                    "followees"
                    ).annotate(
                        followers_total=Count("followers", distinct=True),
                        followees_total=Count("followees", distinct=True)
                    )

        username = self.request.query_params.get("username")
        first_name = self.request.query_params.get("first_name")
        last_name = self.request.query_params.get("last_name")

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

    def get_queryset(self) -> QuerySet[FollowingInteraction]:
        user = self.request.user
        return user.profile.followers.all()


class CurrentUserProfileFolloweesView(generics.ListAPIView):
    serializer_class = FolloweeSerializer

    def get_queryset(self) -> QuerySet[FollowingInteraction]:
        user = self.request.user
        return user.profile.followees.all()


class PostViewSet(viewsets.ModelViewSet):
    permission_classes = (IsOwnerOrReadOnly,)

    def get_queryset(self) -> QuerySet[Post]:
        """
        Returns a QuerySet of Post objects annotated with the total number of
        likes and comments each post has, and also annotated with a boolean
        indicating whether the current user has liked the post.

        The QuerySet is filtered by the query parameters "hashtags" and
        "author_username", if any of them are present.

        :return: A QuerySet of Post objects
        """
        if self.request.user.is_authenticated:
            user_profile = self.request.user.profile
            queryset = (
                Post.objects.select_related("author")
                .prefetch_related(
                    "hashtags",
                    "likes__profile",
                    "comments__author"
                )
                .annotate(
                    likes_count=Subquery(
                        Like.objects.filter(post=OuterRef("pk"))
                        .values("post")
                        .annotate(count=Count("post"))
                        .values("count"),
                    ),
                    comments_count=Subquery(
                        Comment.objects.filter(post=OuterRef("pk"))
                        .values("post")
                        .annotate(count=Count("post"))
                        .values("count"),
                    ),
                    liked_by_user=Exists(
                        Like.objects.filter(
                            post=OuterRef("pk"),
                            profile=user_profile
                        )
                    )
                )
            )
        else:
            queryset = (
                Post.objects.select_related("author")
                .prefetch_related(
                    "hashtags",
                    "likes__profile",
                    "comments__author"
                )
                .annotate(
                    likes_count=Subquery(
                        Like.objects.filter(post=OuterRef("pk"))
                        .values("post")
                        .annotate(count=Count("post"))
                        .values("count"),
                    ),
                    comments_count=Subquery(
                        Comment.objects.filter(post=OuterRef("pk"))
                        .values("post")
                        .annotate(count=Count("post"))
                        .values("count"),
                    ),
                )
            )

        hashtags = self.request.query_params.get("hashtags")
        author_username = self.request.query_params.get("author_username")

        if hashtags:
            hashtag_list = [
                hashtag.strip().lower()
                for hashtag
                in hashtags.split(",")
            ]
            queryset = queryset.filter(hashtags__caption__in=hashtag_list)

        if author_username:
            queryset = queryset.filter(
                author__username__icontains=author_username
            )

        return queryset.distinct()

    def get_serializer_class(self) -> serializers.BaseSerializer:
        if self.action == "list":
            return PostListSerializer
        if self.action == "retrieve":
            return PostDetailSerializer
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

    def create(self, request, *args, **kwargs) -> Response:
        """
        Creates a new post instance with the currently authenticated user
        as the author.
        The method ensures that only authenticated users can create posts by
        overriding the permission_classes attribute of the ViewSet to include
        only the IsAuthenticated permission.
        """
        self.permission_classes = [IsAuthenticated]
        self.check_permissions(request)
        return super().create(request, *args, **kwargs)

    @action(
        detail=True,
        methods=["post"],
        url_path="upload-image",
        permission_classes=[IsAuthenticated, IsOwnerOrReadOnly],
    )
    def upload_image(self, request, pk: int=None) -> Response:
        post = get_object_or_404(Post, pk=pk)
        # with object-level permission, we need to check the permission manually
        self.check_object_permissions(request, post)
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
        permission_classes=[IsAuthenticated],
    )
    def my_posts(self, request) -> Response:
        queryset = self.get_queryset().filter(author=request.user.profile)
        serializer = PostSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="followees-posts",
        permission_classes=[IsAuthenticated],
    )
    def followees_posts(self, request) -> Response:
        user_profile = request.user.profile
        followees_profiles = user_profile.followees.values_list(
            "followee",
            flat=True
        )
        followees_posts = self.get_queryset().filter(author__in=followees_profiles)
        serializer = PostSerializer(followees_posts, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        url_path="like",
        permission_classes=[IsAuthenticated]
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
        permission_classes=[IsAuthenticated]
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
        permission_classes=[IsAuthenticated],
    )
    def liked(self, request) -> Response:
        user_profile = request.user.profile
        liked_posts = self.get_queryset().filter(likes__profile=user_profile)
        serialzer = PostSerializer(liked_posts, many=True)
        return Response(serialzer.data)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (IsOwnerOrReadOnly,)

    def get_queryset(self) -> QuerySet:
        queryset = Comment.objects.filter(
            post_id=self.kwargs["post_pk"]
        ).prefetch_related("author")
        return queryset
    
    def perform_create(self, serializer: CommentSerializer) -> None:
        post = get_object_or_404(Post, pk=self.kwargs.get("post_pk"))
        serializer.save(author=self.request.user.profile, post=post)

    def create(self, request, *args, **kwargs) -> Response:
        """
        Creates a new comment under a post. The comment is created with
        the currently authenticated user as the author.
        """
        self.permission_classes = [IsAuthenticated]
        self.check_permissions(request)
        return super().create(request, *args, **kwargs)
