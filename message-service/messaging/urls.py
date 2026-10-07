from django.urls import re_path

from .views import ContactsView, HistoryView, NotificationView, ReadAllView, SendView

urlpatterns = [
    re_path(r"^contacts/?$", ContactsView.as_view()),
    re_path(r"^notifications/?$", NotificationView.as_view()),
    re_path(r"^notifications/read-all/?$", ReadAllView.as_view()),
    re_path(r"^$", SendView.as_view()),
    re_path(r"^(?P<contact_id>[^/]+)/?$", HistoryView.as_view()),
]
