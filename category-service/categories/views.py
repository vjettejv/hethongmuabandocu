from django.db import DatabaseError
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from categories import selectors, serializers, services
from categories.exceptions import CategoryError


def execute(operation, status=200):
    try:
        return Response(operation(), status=status)
    except CategoryError as error:
        return Response({"error": str(error)}, status=500)
    except DatabaseError:
        return Response({"error": "Internal Server Error"}, status=500)


class CategoriesView(APIView):
    @extend_schema(responses={200: serializers.CategoryResponse(many=True)})
    def get(self, request):
        return execute(lambda: [serializers.projection(row) for row in selectors.all_categories()])

    @extend_schema(
        request=serializers.CategoryFields,
        responses={201: serializers.CategoryResponse, 500: serializers.ErrorResponse},
    )
    def post(self, request):
        return execute(lambda: serializers.projection(services.create_category(request.data)), 201)


class AdminCategoriesView(APIView):
    @extend_schema(
        request=serializers.CategoryFields,
        responses={201: serializers.AdminCategoryResponse, 500: serializers.ErrorResponse},
    )
    def post(self, request):
        return execute(
            lambda: {"data": serializers.projection(services.create_category(request.data))}, 201
        )
