import logging

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from posts import clients, selectors, services, storage
from posts.authentication import authenticate
from posts.exceptions import PostError
from posts.serializers import formatted_response

LOGGER = logging.getLogger("posts.errors")
POST_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "userId": {"type": "integer"},
        "categoryId": {"type": "integer"},
        "price": {"type": "number"},
        "Images": {"type": "array", "items": {"type": "object"}},
        "Category": {"type": "object"},
    },
}
POST_SCHEMA["properties"].update(
    {
        "title": {"type": "string"},
        **{
            key: {"type": "string", "nullable": True}
            for key in ("description", "condition", "status")
        },
        **{key: {"type": "string", "format": "date-time"} for key in ("createdAt", "updatedAt")},
    }
)
POST_SCHEMA["properties"]["status"] = {
    "type": "string",
    "enum": ["pending", "approved", "rejected"],
}
CREATE_SCHEMA = {
    "type": "object",
    "required": ["categoryId", "title", "price"],
    "properties": {
        **{
            key: {"type": "string"}
            for key in ("categoryId", "title", "description", "price", "condition")
        },
        "images": {"type": "array", "maxItems": 5, "items": {"type": "string", "format": "binary"}},
    },
}
CREATE_SCHEMA["properties"]["price"] = {"oneOf": [{"type": "string"}, {"type": "number"}]}
CREATE_SCHEMA["properties"]["categoryId"] = {"oneOf": [{"type": "string"}, {"type": "integer"}]}


class LegacyView(APIView):
    parser_classes = [JSONParser, MultiPartParser]

    def handle_exception(self, error):
        if isinstance(error, PostError):
            body = {"error": str(error)}
            if error.details is not None:
                body["details"] = error.details
            return Response(body, status=error.status)
        LOGGER.error(
            "post failure",
            extra={
                "request_id": getattr(self.request, "request_id", "-"),
                "failure": type(error).__name__,
            },
        )
        return Response({"error": "Internal Server Error"}, status=500)


class PostsView(LegacyView):
    @extend_schema(
        parameters=[OpenApiParameter(key, str) for key in ("categoryId", "keyword", "status")],
        responses={200: {"type": "array", "items": POST_SCHEMA}},
    )
    def get(self, request):
        posts = list(selectors.list_posts(selectors.legacy_parameters(request)))
        categories = clients.categories(request.request_id)
        return Response([formatted_response(post, categories) for post in posts])

    @extend_schema(
        request={"multipart/form-data": CREATE_SCHEMA, "application/json": CREATE_SCHEMA},
        responses={201: dict},
    )
    def post(self, request):
        identity = authenticate(request)
        data = request.data
        files = request.FILES.getlist("images")
        if len(files) > 5 or set(request.FILES) - {"images"}:
            raise PostError("Internal Server Error", details="Unexpected field")
        post = services.create(identity.get("id"), data, files, request.request_id)
        return Response({"message": "Post created successfully", "post": post}, status=201)


class MyPostsView(LegacyView):
    @extend_schema(responses={200: {"type": "array", "items": POST_SCHEMA}})
    def get(self, request):
        identity = authenticate(request)
        if identity.get("id") is None:
            raise PostError("Invalid post data")
        posts = list(selectors.list_posts(user_id=identity["id"]))
        categories = clients.categories(request.request_id)
        return Response([formatted_response(post, categories) for post in posts])


class DetailView(LegacyView):
    @extend_schema(responses={200: POST_SCHEMA, 404: dict})
    def get(self, request, identifier):
        post = selectors.detail(identifier)
        if post is None:
            raise PostError("Post not found", 404)
        return Response(formatted_response(post, clients.categories(request.request_id)))

    @extend_schema(responses={200: dict, 404: dict})
    def delete(self, request, identifier):
        identity = authenticate(request)
        return Response(services.owner_delete(identifier, identity.get("id"), request.request_id))


class AdminPostsView(LegacyView):
    @extend_schema(responses={200: dict})
    def get(self, request):
        authenticate(request)
        posts = list(selectors.list_posts())
        categories = clients.categories(request.request_id)
        return Response({"data": [formatted_response(post, categories) for post in posts]})


class AdminDetailView(LegacyView):
    @extend_schema(
        request={
            "type": "object",
            "required": ["status"],
            "properties": {"status": {"type": "string", "enum": ["approved", "rejected"]}},
        },
        responses={200: dict, 400: dict, 404: dict},
    )
    def put(self, request, identifier):
        authenticate(request)
        return Response({"data": services.moderate(identifier, request.data, request.request_id)})

    @extend_schema(responses={200: dict})
    def delete(self, request, identifier):
        authenticate(request)
        return Response(services.admin_delete(identifier))


class UploadView(APIView):
    @extend_schema(responses={(200, "application/octet-stream"): bytes})
    def get(self, request, filename):
        return storage.serve(request, filename)
