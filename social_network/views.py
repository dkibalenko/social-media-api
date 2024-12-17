from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import viewsets
from rest_framework import generics
from rest_framework import mixins

from social_network.models import Profile
from social_network.serializers import ProfileSerializer


class CurrentUserProfileView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileSerializer

    def get_object(self):
        user_profile = generics.get_object_or_404(
            Profile,
            user=self.request.user
        )
        return user_profile

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
    serializer_class = ProfileSerializer
