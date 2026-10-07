import jwt
from django.conf import settings

from profiles.exceptions import ProfileError


def authenticate(request):
    authorization = request.headers.get("Authorization", "")
    parts = authorization.split()
    if len(parts) < 2:
        raise ProfileError("Unauthorized", 401)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ProfileError("Invalid token", 401)
    try:
        claims = jwt.decode(
            parts[1],
            settings.JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_iat": False, "verify_aud": False},
        )
    except jwt.PyJWTError as error:
        raise ProfileError("Invalid token", 401) from error
    request.auth_identity = claims
    return claims
