from django.urls import re_path

from .views import SearchView, SyncView

urlpatterns = [re_path(r"^$", SearchView.as_view()), re_path(r"^sync/?$", SyncView.as_view())]
