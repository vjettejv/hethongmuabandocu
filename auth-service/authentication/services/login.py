from authentication import selectors
from authentication.exceptions import AuthError
from authentication.services.passwords import verify_password
from authentication.services.tokens import issue_token


def projection(user):
    return {"id": user.id, "username": user.username, "email": user.email, "roleId": user.role_id}


def login(data):
    identifier = data.get("username") or data.get("email")
    user = selectors.by_identifier(identifier) if isinstance(identifier, str) else None
    if not user or not verify_password(data.get("password"), user.password):
        raise AuthError("Invalid credentials", 401)
    # Compatibility: legacy login doesn't require isVerified.
    return {"token": issue_token(user), "user": projection(user)}
