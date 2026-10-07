from pathlib import Path

import environ
from common.logging import build_logging

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
# Environment takes precedence; .env is local-only and excluded from Docker builds.
environ.Env.read_env(BASE_DIR / ".env", overwrite=False)
SERVICE_NAME = env("SERVICE_NAME", default="message-service")
PORT = env.int("PORT", default=3005)
DEBUG = env.bool("DEBUG", default=False)
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1", "testserver", "message-service-python", "message-service"],
)
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
INSTALLED_APPS = ["rest_framework", "drf_spectacular", "messaging.apps.BusinessConfig"]
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
DATABASE_BACKED = True
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "HOST": env("DB_HOST", default="message-db"),
        "PORT": env.int("DB_PORT", default=3306),
        "NAME": env("DB_NAME", default="message_db"),
        "USER": env("DB_USER", default=""),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "CONN_MAX_AGE": 0,
        "OPTIONS": {"connect_timeout": env.int("DB_CONNECT_TIMEOUT", default=3)},
    }
}

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

JWT_SECRET = env("JWT_SECRET", default="")
DEPENDENCY_TIMEOUT = env.float("DEPENDENCY_TIMEOUT", default=3)
REALTIME_TIMEOUT = env.float("REALTIME_TIMEOUT", default=3)
