from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response

from . import selectors, services
from .exceptions import LegacyError
from .http import LegacyView
from .serializers import response

REVIEW = {
    "type": "object",
    "properties": {
        key: {"type": "integer"} for key in ("id", "reviewerId", "revieweeId", "postId", "rating")
    },
}
MULTIPART = {
    "type": "object",
    "properties": {
        **{
            key: {"type": "string"}
            for key in ("reviewerId", "revieweeId", "postId", "rating", "comment")
        },
        "image": {"type": "string", "format": "binary"},
    },
}


def image(request):
    files = request.FILES.getlist("image")
    if len(files) > 1 or set(request.FILES) - {"image"}:
        raise LegacyError("Unexpected field")
    return files[0] if files else None


class ReviewsView(LegacyView):
    @extend_schema(
        request={"multipart/form-data": MULTIPART, "application/json": MULTIPART},
        responses={201: REVIEW},
    )
    def post(self, request):
        return Response(services.create(request.data, image(request)), status=201)


class UserReviewsView(LegacyView):
    @extend_schema(
        parameters=[OpenApiParameter("rating", str), OpenApiParameter("hasImage", str)],
        responses={200: {"type": "array", "items": REVIEW}},
    )
    def get(self, request, userId):
        return Response(
            [response(row) for row in selectors.list_reviews(userId, request.query_params)]
        )


class DetailView(LegacyView):
    @extend_schema(
        request={"multipart/form-data": MULTIPART, "application/json": MULTIPART},
        responses={200: REVIEW, 404: dict},
    )
    def put(self, request, id):
        return Response(services.update(id, request.data, image(request), request.request_id))

    @extend_schema(responses={200: dict, 404: dict})
    def delete(self, request, id):
        return Response(services.delete(id, request.request_id))
