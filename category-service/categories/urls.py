from django.urls import re_path

from categories.views import AdminCategoriesView, CategoriesView

urlpatterns = [
    re_path(r"^$", CategoriesView.as_view(), name="categories"),
    re_path(r"^admin/categories/?$", AdminCategoriesView.as_view(), name="admin-categories"),
]
