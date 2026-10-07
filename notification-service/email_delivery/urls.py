from django.urls import re_path

from .views import EmailView

urlpatterns = [re_path(r"^email/?$", EmailView.as_view())]
