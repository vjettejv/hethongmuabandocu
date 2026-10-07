import time

import jwt
from django.conf import settings

from authentication.exceptions import AuthError


def issue_token(user):
    now = int(time.time())
    return jwt.encode(
        {"id": user.id, "roleId": user.role_id, "iat": now, "exp": now + 86400},
        settings.JWT_SECRET,
        algorithm="HS256",
    )


def verify_token(authorization):
    if not authorization:
        raise AuthError("No token provided", 401)
    parts = authorization.split()
    if len(parts) < 2:
        raise AuthError("No token provided", 401)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthError("Invalid token", 401)
    try:
        claims = jwt.decode(
            parts[1],
            settings.JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_iat": False, "verify_aud": False},
        )
    except jwt.PyJWTError as error:
        raise AuthError("Invalid token", 401) from error
    return {"valid": True, "user": claims}
