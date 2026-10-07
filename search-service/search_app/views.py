from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response

from . import selectors, services
from .http import LegacyView
from .serializers import response

INDEX = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "postId": {"type": "integer"},
        "price": {"type": "string", "nullable": True},
    },
}


class SearchView(LegacyView):
    @extend_schema(
        parameters=[
            OpenApiParameter(key, str) for key in ("query", "categoryId", "minPrice", "maxPrice")
        ],
        responses={200: {"type": "array", "items": INDEX}},
    )
    def get(self, request):
        return Response(
            [response(row) for row in selectors.search(selectors.legacy_parameters(request))]
        )


class SyncView(LegacyView):
    @extend_schema(
        request={
            "type": "object",
            "required": ["postId", "title"],
            "properties": {
                "postId": {"type": "integer"},
                "title": {"type": "string"},
                **{
                    key: {"type": "string", "nullable": True}
                    for key in ("description", "imageUrl", "categoryName", "status")
                },
                "price": {"oneOf": [{"type": "number"}, {"type": "string"}], "nullable": True},
                "categoryId": {"type": "integer", "nullable": True},
            },
        },
        responses={200: dict},
    )
    def post(self, request):
        return Response(services.sync(request.data))
