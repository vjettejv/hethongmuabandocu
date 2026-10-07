import logging

import httpx
from django.conf import settings

logger = logging.getLogger("authentication.dependencies")


def send_dependency(service, method, path, payload, request_id):
    base = settings.SERVICE_URLS[f"{service.upper()}_SERVICE_URL"]
    if not base:
        logger.warning("dependency not configured")
        return
    try:
        with httpx.Client(timeout=settings.INTERNAL_HTTP_TIMEOUT, trust_env=False) as client:
            response = client.request(
                method,
                base.rstrip("/") + path,
                json=payload,
                headers={"X-Request-ID": request_id},
            )
            if not response.is_success:
                logger.warning("dependency returned error")
    except httpx.HTTPError:
        # Match legacy best-effort behavior; no write retries or secret error details.
        logger.warning("dependency unavailable")


def send_otp_email(user, request_id):
    send_dependency(
        "notification",
        "POST",
        "/email",
        {
            "to": user.email,
            "subject": "Mã xác thực OTP - Đồ Cũ Marketplace",
            "text": f"Xin chào {user.username},\n\nMã xác thực OTP của bạn là: {user.otp}\n\n"
            "Vui lòng nhập mã này trên trang web để kích hoạt tài khoản.\n\n"
            "Trân trọng,\nĐội ngũ Đồ Cũ Marketplace",
            "html": f"<h3>Xin chào {user.username},</h3><p>Mã xác thực OTP của bạn là: "
            f'<strong style="font-size:24px;color:blue;">{user.otp}</strong></p>'
            "<p>Vui lòng nhập mã này trên trang web để kích hoạt tài khoản.</p>"
            "<p>Trân trọng,<br>Đội ngũ Đồ Cũ Marketplace</p>",
        },
        request_id,
    )


def create_profile(user, request_id):
    send_dependency("user", "PUT", f"/{user.id}", {"fullName": user.username}, request_id)
