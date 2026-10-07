from email import policy
from email.parser import BytesParser

import pytest
from conftest import compare


@pytest.mark.parametrize("mode", ["development", "production-mock", "missing-user"])
@pytest.mark.parametrize(
    "body",
    [
        {},
        {"to": "receiver@example.invalid"},
        {"subject": "synthetic"},
        {"to": "receiver@example.invalid", "subject": "synthetic", "text": "tiếng Việt"},
        {"to": "receiver@example.invalid", "subject": "synthetic", "html": "<b>synthetic</b>"},
    ],
)
def test_mock_condition_and_missing_payload_parity(live, mode, body):
    client, urls = live
    responses = [client.post(url + "/email", json=body) for url in urls["email"][mode].values()]
    assert all(r.status_code == 200 for r in responses)
    compare(responses[0].json(), responses[1].json())
    assert responses[1].json() == {"message": "Email queued (Mock)", "mock": True}


@pytest.mark.parametrize(
    "parts",
    [
        {"text": "synthetic tiếng Việt 💬"},
        {"html": "<b>synthetic tiếng Việt</b>"},
        {"text": "synthetic plain", "html": "<b>synthetic html</b>"},
    ],
)
def test_real_local_smtp_transport_envelope_and_mime(live, parts):
    client, urls = live
    payload = {
        "to": "Receiver <receiver@example.invalid>",
        "subject": "synthetic phase6 tiếng Việt",
        **parts,
    }
    for runtime in ("node", "python"):
        response = client.post(urls["email"]["smtp"][runtime] + "/email", json=payload)
        assert response.status_code == 200
        assert response.json()["message"] == "Email sent successfully"
        assert response.json()["messageId"].startswith("<") and response.json()[
            "messageId"
        ].endswith(">")
        captured = client.get(urls["smtp"] + "/__messages").json()["messages"][-1]
        # ESMTP permits MAIL FROM SIZE parameters; the envelope address is exact.
        assert captured["from"].split()[0] == "<sender@phase6.local.test>" and captured["to"] == [
            "<receiver@example.invalid>"
        ]
        message = BytesParser(policy=policy.default).parsebytes(captured["body"].encode("utf-8"))
        assert message["Message-ID"] == response.json()["messageId"]
        assert str(message["Subject"]) == payload["subject"]
        assert "Đồ Cũ Marketplace" in str(message["From"])
        for kind, value in parts.items():
            actual = message.get_body(
                preferencelist=("plain" if kind == "text" else "html",)
            ).get_content()
            assert actual.rstrip() == value


def test_real_smtp_missing_recipient_parity(live):
    client, urls = live
    responses = [
        client.post(url + "/email", json={"subject": "synthetic"})
        for url in urls["email"]["smtp"].values()
    ]
    assert all(r.status_code == 500 for r in responses)
    compare(responses[0].json(), responses[1].json())


def test_real_smtp_failure_safe_divergence(live):
    client, urls = live
    client.post(urls["smtp"] + "/__control", json={"reject": True})
    responses = [
        client.post(url + "/email", json={"to": "receiver@example.invalid", "text": "synthetic"})
        for url in urls["email"]["smtp"].values()
    ]
    assert all(r.status_code == 500 for r in responses)
    assert responses[1].json() == {"error": "Email delivery failed"}
    assert client.get(urls["smtp"] + "/__messages").json()["messages"] == []
