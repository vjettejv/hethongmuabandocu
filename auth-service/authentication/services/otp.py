import secrets

from django.utils import timezone

from authentication import selectors
from authentication.exceptions import AuthError
from authentication.services import clients


def verify_otp(data, request_id):
    user = selectors.by_email(data.get("email"))
    if not user:
        raise AuthError("User not found", 404)
    supplied = data.get("otp")
    if (
        not isinstance(supplied, str)
        or not user.otp
        or not secrets.compare_digest(user.otp.encode("utf-8"), supplied.encode("utf-8"))
    ):
        # No bypass; normalize legacy's mojibake/error mismatch intentionally.
        raise AuthError("Mã OTP không chính xác", 400)
    user.is_verified, user.otp, user.updated_at = True, None, timezone.now()
    user.save(update_fields=["is_verified", "otp", "updated_at"])
    clients.create_profile(user, request_id)
    return {"message": "Verified successfully"}
