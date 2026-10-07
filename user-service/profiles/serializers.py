from datetime import UTC

from rest_framework import serializers


def timestamp(value):
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def projection(profile):
    data = {
        "id": profile.id,
        "authId": getattr(profile, "_response_auth_id", profile.auth_id),
        "fullName": profile.full_name,
        "phone": profile.phone,
        "address": profile.address,
        "avatar": profile.avatar,
        "createdAt": timestamp(profile.created_at),
        "updatedAt": timestamp(profile.updated_at),
    }
    for field in getattr(profile, "_omitted_response_fields", ()):
        data.pop(field, None)
    return data


class ProfileFields(serializers.Serializer):
    fullName = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    phone = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    address = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    avatar = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class ProfileResponse(ProfileFields):
    id = serializers.IntegerField()
    authId = serializers.JSONField(
        help_text="Numeric after lookup; decimal string after URL create."
    )
    createdAt = serializers.DateTimeField()
    updatedAt = serializers.DateTimeField()


class ErrorResponse(serializers.Serializer):
    error = serializers.CharField()
