from pathlib import Path

import environ
from common.logging import build_logging

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
# Environment takes precedence; .env is local-only and excluded from Docker builds.
environ.Env.read_env(BASE_DIR / ".env", overwrite=False)
SERVICE_NAME = env("SERVICE_NAME", default="notification-service")
PORT = env.int("PORT", default=3006)
DEBUG = env.bool("DEBUG", default=False)
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[
        "localhost",
        "127.0.0.1",
        "testserver",
        "notification-service-python",
        "notification-service",
    ],
)
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
INSTALLED_APPS = ["rest_framework", "drf_spectacular", "email_delivery.apps.BusinessConfig"]
MIDDLEWARE = ["common.middleware.RequestContextMiddleware"]
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True}]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
APPEND_SLASH = False
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
DATABASE_BACKED = False
DATABASES = {}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
    "UNAUTHENTICATED_TOKEN": None,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}
SPECTACULAR_SETTINGS = {
    "TITLE": SERVICE_NAME,
    "VERSION": "phase-6",
    "DESCRIPTION": "Legacy-compatible Phase 6 business endpoints.",
    "SERVE_INCLUDE_SCHEMA": False,
}
SERVICE_URLS = {
    key: env(key, default="")
    for key in (
        "AUTH_SERVICE_URL",
        "USER_SERVICE_URL",
        "POST_SERVICE_URL",
        "CATEGORY_SERVICE_URL",
        "MESSAGE_SERVICE_URL",
        "NOTIFICATION_SERVICE_URL",
        "REVIEW_SERVICE_URL",
        "SEARCH_SERVICE_URL",
        "FAVORITE_SERVICE_URL",
    )
}
LOGGING = build_logging(SERVICE_NAME)

NODE_ENV = env("NODE_ENV", default="development")
MOCK_EMAIL = env("MOCK_EMAIL", default="")
SMTP_HOST = env("SMTP_HOST", default="smtp.example.com")
SMTP_PORT = env.int("SMTP_PORT", default=587)
SMTP_USER = env("SMTP_USER", default="")
SMTP_PASS = env("SMTP_PASS", default="")
SMTP_TIMEOUT = env.float("SMTP_TIMEOUT", default=3)
