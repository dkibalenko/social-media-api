from django.db.models import Count
from django.db.models.query import QuerySet

from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import viewsets
from rest_framework import generics
from rest_framework import mixins

from social_network.models import Profile
from social_network.serializers import ProfileSerializer, ProfileListSerializer


class CurrentUserProfileView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileSerializer

    def get_object(self) -> Profile:
        return generics.get_object_or_404(self.get_queryset())
    
    def get_queryset(self) -> QuerySet[Profile]:
        return (
            Profile.objects.filter(user=self.request.user)
            .prefetch_related("following", "followers")
            .annotate(
                followers_total=Count("followers"),
                following_total=Count("following")
            )
        )

    def destroy(self, request, *args, **kwargs):
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

    def get_queryset(self):
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
