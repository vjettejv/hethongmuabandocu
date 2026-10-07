from drf_spectacular.utils import extend_schema
from rest_framework.response import Response

from . import clients, selectors, services
from .authentication import authenticate
from .http import LegacyView


class ToggleView(LegacyView):
    @extend_schema(
        request={
            "type": "object",
            "required": ["postId"],
            "properties": {"postId": {"type": "integer"}},
        },
        responses={200: dict, 201: dict},
    )
    def post(self, request):
        result = services.toggle(authenticate(request).get("id"), request.data)
        return Response(result, status=201 if result["isFavorited"] else 200)


class CheckView(LegacyView):
    @extend_schema(responses={200: dict})
    def get(self, request, postId):
        return Response({"isFavorited": selectors.check(authenticate(request).get("id"), postId)})


class FavoritesView(LegacyView):
    @extend_schema(responses={200: {"type": "array", "items": {"type": "object"}}})
    def get(self, request):
        identifiers = list(
            selectors.rows(authenticate(request).get("id")).values_list("postId", flat=True)
        )
        return Response(clients.hydrate(identifiers, request.request_id) if identifiers else [])
