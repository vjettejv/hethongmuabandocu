from django.apps import AppConfig


class BusinessConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "authentication"
    verbose_name = "auth-service foundation (no business models)"
