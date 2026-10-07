from django.apps import AppConfig


class BusinessConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "posts"
    verbose_name = "post-service foundation (no business models)"
