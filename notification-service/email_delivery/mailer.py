import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, getaddresses, make_msgid

from django.conf import settings

from .exceptions import LegacyError


def send(data):
    raw = data.get("to", [])
    raw = raw if isinstance(raw, list) else [raw]
    names = [
        formataddr((item.get("name", ""), item["address"])) if isinstance(item, dict) else item
        for item in raw
        if item
    ]
    recipients = [address for _, address in getaddresses(names) if address]
    if not recipients:
        raise LegacyError("No recipients defined")
    message = EmailMessage()
    message["From"] = formataddr(("Đồ Cũ Marketplace", settings.SMTP_USER or "noreply@docu.com"))
    message["To"] = ", ".join(names)
    if data.get("subject") is not None:
        message["Subject"] = str(data["subject"])
    message["Message-ID"] = make_msgid()
    if data.get("html") and not data.get("text"):
        message.set_content(data["html"], subtype="html")
    else:
        message.set_content(data.get("text") or "")
        if data.get("html"):
            message.add_alternative(data["html"], subtype="html")
    with smtplib.SMTP(
        settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT
    ) as smtp:
        smtp.ehlo()
        if smtp.has_extn("starttls"):
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
        smtp.login(settings.SMTP_USER, settings.SMTP_PASS)
        smtp.send_message(message, from_addr=settings.SMTP_USER, to_addrs=recipients)
    return str(message["Message-ID"])
