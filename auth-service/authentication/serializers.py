from rest_framework import serializers


class RegisterRequest(serializers.Serializer):
    username = serializers.CharField(trim_whitespace=False)
    email = serializers.CharField(trim_whitespace=False)
    password = serializers.CharField(trim_whitespace=False, write_only=True)


class LoginRequest(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)
    email = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)
    password = serializers.CharField(trim_whitespace=False, write_only=True)


class OtpRequest(serializers.Serializer):
    email = serializers.CharField(trim_whitespace=False)
    otp = serializers.CharField(trim_whitespace=False, write_only=True)


class UserResponse(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.CharField()
    roleId = serializers.IntegerField(allow_null=True)


class ErrorResponse(serializers.Serializer):
    error = serializers.CharField()


class MessageResponse(serializers.Serializer):
    message = serializers.CharField()


class RegisterResponse(MessageResponse):
    userId = serializers.IntegerField()


class LoginResponse(serializers.Serializer):
    token = serializers.CharField()
    user = UserResponse()


class ClaimsResponse(serializers.Serializer):
    id = serializers.IntegerField()
    roleId = serializers.IntegerField(allow_null=True)
    iat = serializers.IntegerField()
    exp = serializers.IntegerField()


class VerifyResponse(serializers.Serializer):
    valid = serializers.BooleanField()
    user = ClaimsResponse()
