import logging

from django.conf import settings

from . import mailer
from .exceptions import LegacyError

LOGGER = logging.getLogger("email_delivery")


def send(data, request_id):
    if settings.NODE_ENV != "production" or settings.MOCK_EMAIL == "true" or not settings.SMTP_USER:
        LOGGER.info("mock email accepted", extra={"request_id": request_id, "email_mode": "mock"})
        return {"message": "Email queued (Mock)", "mock": True}
    try:
        identifier = mailer.send(data)
    except LegacyError:
        raise
    except Exception as error:
        LOGGER.warning(
            "email delivery failed",
            extra={"request_id": request_id, "email_mode": "smtp", "failure": type(error).__name__},
        )
        raise LegacyError("Email delivery failed") from error
    LOGGER.info("email delivered", extra={"request_id": request_id, "email_mode": "smtp"})
    return {"message": "Email sent successfully", "messageId": identifier}
