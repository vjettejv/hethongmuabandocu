from django.apps import AppConfig


class BusinessConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "messaging"
    verbose_name = "message-service foundation (no business models)"
