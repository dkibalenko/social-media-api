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

from social_network.models import FollowingInteraction, Profile
from social_network.serializers import (
    ProfileSerializer,
    ProfileListSerializer,
    ProfileDetailSerializer,
    EmptySerializer,
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
