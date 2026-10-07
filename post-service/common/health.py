from django.conf import settings
from django.db import DatabaseError, InterfaceError, connection
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

HealthResponse = inline_serializer(
    "HealthResponse",
    fields={
        "service": serializers.CharField(),
        "status": serializers.ChoiceField(choices=["healthy"]),
    },
)
ReadyResponse = inline_serializer(
    "ReadyResponse",
    fields={
        "service": serializers.CharField(),
        "status": serializers.ChoiceField(choices=["ready", "not_ready"]),
        "database": serializers.ChoiceField(choices=["connected", "unavailable"], required=False),
    },
)


def database_connected():
    # SELECT 1 only: no schema/data writes, migrations or Django system tables.
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return cursor.fetchone() == (1,)
    except (DatabaseError, InterfaceError):
        return False


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(responses={200: HealthResponse}, tags=["foundation"])
    def get(self, request):
        return Response({"service": settings.SERVICE_NAME, "status": "healthy"})


class ReadyView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(responses={200: ReadyResponse, 503: ReadyResponse}, tags=["foundation"])
    def get(self, request):
        if not settings.DATABASE_BACKED:
            return Response({"service": settings.SERVICE_NAME, "status": "ready"})
        connected = database_connected()
        return Response(
            {
                "service": settings.SERVICE_NAME,
                "status": "ready" if connected else "not_ready",
                "database": "connected" if connected else "unavailable",
            },
            status=200 if connected else 503,
        )
