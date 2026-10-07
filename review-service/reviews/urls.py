from django.urls import re_path

from .views import DetailView, ReviewsView, UserReviewsView

urlpatterns = [
    re_path(r"^$", ReviewsView.as_view()),
    re_path(r"^user/(?P<userId>[^/]+)/?$", UserReviewsView.as_view()),
    re_path(r"^(?P<id>[^/]+)/?$", DetailView.as_view()),
]
