from email.message import EmailMessage
from unittest.mock import MagicMock

import pytest
from django.conf import settings
from email_delivery import mailer, services
from email_delivery.exceptions import LegacyError


@pytest.mark.parametrize(
    "node_env,mock,user",
    [
        ("development", "false", "synthetic@local.test"),
        ("production", "true", "synthetic@local.test"),
        ("production", "false", ""),
    ],
)
@pytest.mark.parametrize(
    "body",
    [
        {},
        {"to": "receiver@local.test"},
        {"subject": "phase6_test"},
        {"to": "receiver@local.test", "subject": "phase6_test", "html": "<b>synthetic</b>"},
    ],
)
def test_exact_mock_conditions_and_optional_fields(client, monkeypatch, node_env, mock, user, body):
    monkeypatch.setattr(settings, "NODE_ENV", node_env)
    monkeypatch.setattr(settings, "MOCK_EMAIL", mock)
    monkeypatch.setattr(settings, "SMTP_USER", user)
    monkeypatch.setattr(mailer, "send", lambda _: pytest.fail("mock must not deliver"))
    response = client.post("/email", data=body, content_type="application/json")
    assert response.status_code == 200 and response.json() == {
        "message": "Email queued (Mock)",
        "mock": True,
    }


@pytest.mark.parametrize(
    "data",
    [
        {"text": "phase6_test"},
        {"html": "<b>phase6_test</b>"},
        {"text": "phase6_test", "html": "<b>phase6_test</b>"},
    ],
)
@pytest.mark.parametrize("tls", [False, True])
def test_smtp_payload_auth_starttls_and_response(monkeypatch, data, tls):
    for key, value in {
        "NODE_ENV": "production",
        "MOCK_EMAIL": "false",
        "SMTP_USER": "sender@local.test",
        "SMTP_PASS": "synthetic-only",
    }.items():
        monkeypatch.setattr(settings, key, value)
    smtp = MagicMock()
    smtp.has_extn.return_value = tls
    context = MagicMock()
    context.__enter__.return_value = smtp
    monkeypatch.setattr(mailer.smtplib, "SMTP", lambda *args, **kwargs: context)
    result = services.send(
        {"to": "receiver@local.test", "subject": "phase6_test"} | data, "safe-request"
    )
    assert result["message"] == "Email sent successfully" and result["messageId"].startswith("<")
    smtp.login.assert_called_once_with("sender@local.test", "synthetic-only")
    assert smtp.starttls.call_count == int(tls)
    message = smtp.send_message.call_args.args[0]
    assert isinstance(message, EmailMessage) and message["Subject"] == "phase6_test"
    assert smtp.send_message.call_args.kwargs["to_addrs"] == ["receiver@local.test"]
    if "html" in data:
        assert "phase6_test" in message.get_body(preferencelist=("html",)).get_content()


def test_smtp_failure_safe_and_missing_recipient(monkeypatch):
    for key, value in {
        "NODE_ENV": "production",
        "MOCK_EMAIL": "false",
        "SMTP_USER": "sender@local.test",
    }.items():
        monkeypatch.setattr(settings, key, value)
    with pytest.raises(LegacyError, match="No recipients defined"):
        services.send({}, "safe-request")

    def fail(data):
        raise RuntimeError("SMTP_PASS=private OTP=private")

    monkeypatch.setattr(mailer, "send", fail)
    with pytest.raises(LegacyError, match="^Email delivery failed$"):
        services.send({"to": "receiver@local.test"}, "safe-request")
