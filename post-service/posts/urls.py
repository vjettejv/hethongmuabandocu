from django.urls import re_path

from posts import views

urlpatterns = [
    re_path(r"^$", views.PostsView.as_view()),
    re_path(r"^my-posts/?$", views.MyPostsView.as_view()),
    re_path(r"^admin/posts/?$", views.AdminPostsView.as_view()),
    re_path(r"^admin/posts/(?P<identifier>[^/]+)/?$", views.AdminDetailView.as_view()),
    re_path(r"^uploads/(?P<filename>.+)$", views.UploadView.as_view()),
    re_path(r"^(?P<identifier>[^/]+)/?$", views.DetailView.as_view()),
]
