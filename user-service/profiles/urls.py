from django.urls import re_path

from profiles.views import MyProfileView, ProfileView

urlpatterns = [
    re_path(r"^me/?$", MyProfileView.as_view(), name="my-profile"),
    re_path(r"^(?P<auth_id>[^/]+)/?$", ProfileView.as_view(), name="profile"),
]
