from django.urls import re_path

from .views import CheckView, FavoritesView, ToggleView

urlpatterns = [
    re_path(r"^toggle/?$", ToggleView.as_view()),
    re_path(r"^check/(?P<postId>[^/]+)/?$", CheckView.as_view()),
    re_path(r"^my-favorites/?$", FavoritesView.as_view()),
]
