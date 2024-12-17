from django.urls import path, include
from rest_framework import routers

from social_network import views

app_name = "social_network"

router = routers.DefaultRouter()

router.register("profiles", views.ProfileViewSet, basename="profiles")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "me/",
        views.CurrentUserProfileView.as_view(),
        name="me"
    )
]
