from datetime import UTC

from rest_framework import serializers


def timestamp(value):
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def projection(category):
    data = {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "createdAt": timestamp(category.created_at),
        "updatedAt": timestamp(category.updated_at),
    }
    if getattr(category, "_description_omitted", False):
        data.pop("description")
    return data


class CategoryFields(serializers.Serializer):
    name = serializers.CharField(allow_blank=True)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class CategoryResponse(CategoryFields):
    id = serializers.IntegerField()
    createdAt = serializers.DateTimeField()
    updatedAt = serializers.DateTimeField()


class AdminCategoryResponse(serializers.Serializer):
    data = CategoryResponse()


class ErrorResponse(serializers.Serializer):
    error = serializers.CharField()
