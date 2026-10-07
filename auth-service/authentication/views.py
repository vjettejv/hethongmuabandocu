from django.db import DatabaseError
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication import selectors, serializers
from authentication.exceptions import AuthError
from authentication.services.login import login, projection
from authentication.services.otp import verify_otp
from authentication.services.registration import register
from authentication.services.tokens import verify_token


def execute(operation, success_status=200):
    try:
        return Response(operation(), status=success_status)
    except AuthError as error:
        return Response({error.envelope: str(error)}, status=error.status)
    except DatabaseError:
        # Database exception strings may contain data and connection credentials.
        return Response({"error": "Internal Server Error"}, status=500)


class RegisterView(APIView):
    @extend_schema(
        request=serializers.RegisterRequest,
        responses={
            201: serializers.RegisterResponse,
            400: serializers.MessageResponse,
            500: serializers.ErrorResponse,
        },
    )
    def post(self, request):
        return execute(lambda: register(request.data, request.request_id), 201)


class LoginView(APIView):
    @extend_schema(
        request=serializers.LoginRequest,
        responses={
            200: serializers.LoginResponse,
            401: serializers.ErrorResponse,
            500: serializers.ErrorResponse,
        },
    )
    def post(self, request):
        return execute(lambda: login(request.data))


class OtpView(APIView):
    @extend_schema(
        request=serializers.OtpRequest,
        responses={
            200: serializers.MessageResponse,
            400: serializers.ErrorResponse,
            404: serializers.ErrorResponse,
            500: serializers.ErrorResponse,
        },
    )
    def post(self, request):
        return execute(lambda: verify_otp(request.data, request.request_id))


class UserView(APIView):
    @extend_schema(
        responses={
            200: serializers.UserResponse,
            404: serializers.ErrorResponse,
            500: serializers.ErrorResponse,
        }
    )
    def get(self, request, identifier):
        def retrieve():
            user = selectors.by_id(identifier)
            if not user:
                raise AuthError("User not found", 404)
            return projection(user)

        return execute(retrieve)


class VerifyView(APIView):
    @extend_schema(
        request=None,
        parameters=[
            OpenApiParameter(
                "Authorization",
                str,
                OpenApiParameter.HEADER,
                required=True,
                description="Bearer <HS256 JWT>",
            )
        ],
        responses={200: serializers.VerifyResponse, 401: serializers.ErrorResponse},
    )
    def post(self, request):
        return execute(lambda: verify_token(request.headers.get("Authorization")))
