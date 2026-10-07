from django.db import DatabaseError
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from profiles import selectors, serializers, services
from profiles.authentication import authenticate
from profiles.exceptions import ProfileError


def execute(operation):
    try:
        return Response(operation())
    except ProfileError as error:
        return Response({"error": str(error)}, status=error.status)
    except DatabaseError:
        return Response({"error": "Internal Server Error"}, status=500)


AUTHORIZATION = OpenApiParameter(
    "Authorization", str, OpenApiParameter.HEADER, required=True, description="Bearer <HS256 JWT>"
)
RESPONSES = {
    200: serializers.ProfileResponse,
    401: serializers.ErrorResponse,
    500: serializers.ErrorResponse,
}


class MyProfileView(APIView):
    @extend_schema(
        parameters=[AUTHORIZATION],
        responses=RESPONSES,
        description="Returns a camelCase profile, or {} when no profile/lookup error exists.",
    )
    def get(self, request):
        def retrieve():
            identity = authenticate(request)
            try:
                profile = selectors.by_auth_id(identity.get("id"))
                return serializers.projection(profile) if profile else {}
            except DatabaseError:
                # The legacy /me GET swallows profile lookup errors after authenticating.
                return {}

        return execute(retrieve)

    @extend_schema(
        parameters=[AUTHORIZATION], request=serializers.ProfileFields, responses=RESPONSES
    )
    def put(self, request):
        def update():
            identity = authenticate(request)
            return serializers.projection(services.update_profile(identity.get("id"), request.data))

        return execute(update)


class ProfileView(APIView):
    @extend_schema(responses={200: serializers.ProfileResponse, 404: serializers.ErrorResponse})
    def get(self, request, auth_id):
        def retrieve():
            profile = selectors.by_auth_id(auth_id)
            if not profile:
                raise ProfileError("Profile not found", 404)
            return serializers.projection(profile)

        return execute(retrieve)

    @extend_schema(request=serializers.ProfileFields, responses=RESPONSES)
    def put(self, request, auth_id):
        # Public by legacy contract, including the Auth OTP profile creation call.
        return execute(
            lambda: serializers.projection(services.update_profile(auth_id, request.data))
        )
