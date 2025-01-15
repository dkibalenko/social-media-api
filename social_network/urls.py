from django.urls import path, include
from rest_framework_nested import routers

from social_network import views

app_name = "social_network"

router = routers.DefaultRouter()

router.register("profiles", views.ProfileViewSet, basename="profiles")
router.register("posts", views.PostViewSet, basename="posts")

posts_router = routers.NestedSimpleRouter(router, "posts", lookup="post")
posts_router.register(
    "comments",
    views.CommentViewSet,
    basename="post-comments"
)

urlpatterns = [
    path("", include(router.urls)),
    path("", include(posts_router.urls)),
    path("me/", views.CurrentUserProfileView.as_view(), name="me"),
    path(
        "me/followers/",
        views.CurrentUserProfileFollowersView.as_view(),
        name="me-followers",
    ),
    path(
        "me/followees/",
        views.CurrentUserProfileFolloweesView.as_view(),
        name="me-followees",
    ),
]
