import secrets

from django.utils import timezone

from authentication import selectors
from authentication.exceptions import AuthError
from authentication.models import AuthUser
from authentication.services import clients, passwords


def register(data, request_id):
    username, email, password = (data.get(key) for key in ("username", "email", "password"))
    if not all(isinstance(value, str) and value for value in (username, email, password)):
        raise AuthError("Vui lòng điền đầy đủ thông tin", 400, "message")
    user = selectors.for_registration(username, email)
    if user and user.is_verified:
        message = "Email đã được sử dụng" if user.email == email else "Tên đăng nhập đã tồn tại"
        raise AuthError(message, 400, "message")
    now = timezone.now()
    encoded = passwords.hash_password(password)
    otp = str(secrets.randbelow(900000) + 100000)
    if user:
        user.username, user.email, user.password, user.otp = username, email, encoded, otp
        user.updated_at = now
        user.save(update_fields=["username", "email", "password", "otp", "updated_at"])
    else:
        user = AuthUser.objects.create(
            username=username,
            email=email,
            password=encoded,
            otp=otp,
            created_at=now,
            updated_at=now,
        )
    clients.send_otp_email(user, request_id)
    return {"message": "User created successfully", "userId": user.id}
