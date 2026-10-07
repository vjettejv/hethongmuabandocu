import logging

import httpx
from django.conf import settings

LOGGER = logging.getLogger("messaging.dependencies")


def exchange(dependency, method, suffix, request_id, payload=None):
    try:
        with httpx.Client(timeout=settings.DEPENDENCY_TIMEOUT, trust_env=False) as client:
            response = client.request(
                method,
                settings.SERVICE_URLS[dependency + "_SERVICE_URL"].rstrip("/") + suffix,
                headers={"X-Request-ID": request_id},
                json=payload,
            )
        LOGGER.info(
            "dependency response",
            extra={
                "request_id": request_id,
                "dependency": dependency,
                "status_code": response.status_code,
            },
        )
        return response
    except (httpx.HTTPError, ValueError):
        LOGGER.warning(
            "dependency unavailable",
            extra={"request_id": request_id, "dependency": dependency, "failure": "unavailable"},
        )
        return None


def user(identifier, request_id):
    fallback = {"id": identifier, "username": f"User {identifier}"}
    response = exchange("USER", "GET", f"/{identifier}", request_id)
    try:
        if response is not None and response.is_success:
            profile = response.json()
            result = {"id": identifier}
            if "fullName" in profile:
                result.update(fullName=profile["fullName"], username=profile["fullName"])
            return result
    except (ValueError, TypeError):
        pass
    return fallback


def email(receiver_id, content, request_id):
    response = exchange("AUTH", "GET", f"/{receiver_id}", request_id)
    try:
        account = response.json() if response is not None and response.is_success else {}
        if account.get("email"):
            # Legacy awaits the email request, but ignores its HTTP error status.
            exchange(
                "NOTIFICATION",
                "POST",
                "/email",
                request_id,
                {
                    "to": account["email"],
                    "subject": "Bạn có tin nhắn mới trên Đồ Cũ",
                    "text": "Bạn vừa nhận được một tin nhắn mới.\n\n"
                    + f"Nội dung: {content}\n\nHãy đăng nhập để trả lời!",
                },
            )
    except (ValueError, TypeError, AttributeError):
        LOGGER.warning(
            "account response invalid",
            extra={"request_id": request_id, "dependency": "AUTH", "failure": "invalid_json"},
        )
