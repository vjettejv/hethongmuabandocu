import asyncio
from datetime import UTC, datetime
from unittest.mock import MagicMock

import httpx
import jwt
import pytest
from django.conf import settings
from messaging import clients, realtime, selectors, services
from messaging.asgi import LegacyUpgradePackets
from messaging.models import Message, Notification
from messaging.serializers import projection


@pytest.mark.parametrize(
    "scope,drop",
    [
        (
            {
                "type": "websocket",
                "path": "/socket.io/",
                "query_string": b"EIO=4&transport=websocket&sid=test",
            },
            True,
        ),
        (
            {
                "type": "websocket",
                "path": "/socket.io/",
                "query_string": b"EIO=4&transport=websocket",
            },
            False,
        ),
        (
            {
                "type": "http",
                "path": "/socket.io/",
                "query_string": b"EIO=4&transport=polling&sid=test",
            },
            False,
        ),
        (
            {
                "type": "websocket",
                "path": "/other/",
                "query_string": b"EIO=4&transport=websocket&sid=test",
            },
            False,
        ),
    ],
)
def test_upgrade_control_packet_order_preserves_other_frames(scope, drop):
    frames = [
        {"type": "websocket.accept"},
        *[
            {"type": "websocket.send", "text": text}
            for text in ["3probe", "6", '40{"sid":"test"}', "2", '42["event","6"]']
        ],
        {"type": "websocket.send", "bytes": b"6"},
        {"type": "websocket.close"},
    ]
    sent = []

    async def app(scope, receive, send):
        for frame in frames:
            await send(frame)

    async def send(frame):
        sent.append(frame)

    asyncio.run(LegacyUpgradePackets(app)(scope, None, send))
    assert sent == [frame for frame in frames if not (drop and frame.get("text") == "6")]


def row(model=Message, **values):
    defaults = {
        "id": 1,
        "isRead": False,
        "createdAt": datetime(2026, 1, 1, tzinfo=UTC),
        "updatedAt": datetime(2026, 1, 1, tzinfo=UTC),
    }
    defaults.update(
        {"senderId": 1, "receiverId": 2, "content": "phase6_test"}
        if model == Message
        else {"userId": 2, "title": "phase6_test", "message": "phase6_test", "link": None}
    )
    return model(**(defaults | values))


def auth(identifier=1):
    token = jwt.encode({"id": identifier, "roleId": 1}, settings.JWT_SECRET, algorithm="HS256")
    return {"HTTP_AUTHORIZATION": "Bearer " + token}


def test_unmanaged_mapping_and_camelcase():
    for model, table in [(Message, "messages"), (Notification, "notifications")]:
        assert not model._meta.managed and model._meta.db_table == table
        assert all(
            not field.is_relation and field.column == field.name for field in model._meta.fields
        )
        data = projection(row(model))
        assert data["createdAt"] == "2026-01-01T00:00:00.000Z" and data["isRead"] is False


@pytest.mark.parametrize(
    "path,method",
    [
        ("/", "post"),
        ("/contacts", "get"),
        ("/2", "get"),
        ("/notifications", "get"),
        ("/notifications/read-all", "put"),
    ],
)
@pytest.mark.parametrize("authorization", [None, "Bearer invalid"])
def test_protected_routes(client, path, method, authorization):
    response = getattr(client, method)(
        path, **({"HTTP_AUTHORIZATION": authorization} if authorization else {})
    )
    assert response.status_code == 401
    assert response.json() == {
        "error": "Unauthorized" if authorization is None else "Invalid token"
    }


def test_sender_claim_and_persist_email_emit_order(client, monkeypatch):
    events = []

    def create(**values):
        events.append("db")
        return row(**values)

    monkeypatch.setattr(Message.objects, "create", create)
    monkeypatch.setattr(clients, "email", lambda *args: events.append("email"))
    monkeypatch.setattr(realtime, "emit", lambda *args: events.append("emit"))
    response = client.post(
        "/",
        data={"receiverId": 2, "senderId": 999, "content": "phase6_test"},
        content_type="application/json",
        **auth(),
    )
    assert response.status_code == 200 and response.json()["data"]["senderId"] == 1
    assert events == ["db", "email", "emit"]


@pytest.mark.parametrize("body", [{}, {"receiverId": 2}, {"content": "phase6_test"}])
def test_missing_message_fields_legacy500(client, body):
    response = client.post("/", data=body, content_type="application/json", **auth())
    assert response.status_code == 500 and "notNull Violation" in response.json()["error"]


def test_notification_public_persist_before_emit(client, monkeypatch):
    events = []
    monkeypatch.setattr(
        Notification.objects,
        "create",
        lambda **values: events.append("db") or row(Notification, **values),
    )
    monkeypatch.setattr(realtime, "emit", lambda *args: events.append(args))
    response = client.post(
        "/notifications",
        data={"receiverId": 2, "title": "phase6_test", "message": "phase6_test"},
        content_type="application/json",
    )
    assert response.status_code == 200 and response.json()["success"] is True
    assert "link" not in response.json()["data"] and events[0] == "db"
    assert events[1][0] == "receive_notification" and events[1][2] == 2


def test_static_notification_route_reachable(client, monkeypatch):
    monkeypatch.setattr(selectors, "notifications", lambda user_id: [{"userId": user_id, "id": 5}])
    monkeypatch.setattr(selectors, "history", lambda *args: pytest.fail("shadowed list"))
    response = client.get("/notifications", **auth())
    assert response.json() == {"data": [{"userId": 1, "id": 5}]}


def test_read_all_owned_filter(monkeypatch):
    manager = MagicMock()
    monkeypatch.setattr(Notification, "objects", manager)
    assert services.read_all(2) == {"success": True}
    manager.filter.assert_called_once_with(userId=2, isRead=False)
    assert manager.filter.return_value.update.call_args.kwargs["isRead"] is True


@pytest.mark.parametrize(
    "response", [None, httpx.Response(404), httpx.Response(200, content=b"invalid")]
)
def test_profile_missing_or_unavailable_fallback(monkeypatch, response):
    monkeypatch.setattr(clients, "exchange", lambda *args: response)
    assert clients.user(5, "safe-request") == {"id": 5, "username": "User 5"}


def test_contacts_numeric_key_order_and_latest(monkeypatch):
    manager = MagicMock()
    manager.filter.return_value.order_by.return_value = [
        row(receiverId=8),
        row(receiverId=3),
        row(receiverId=8, content="older"),
    ]
    monkeypatch.setattr(Message, "objects", manager)
    monkeypatch.setattr(clients, "user", lambda identifier, _: {"id": identifier})
    data = selectors.contacts(1, "safe-request")
    assert [item["id"] for item in data] == [3, 8]
    assert data[1]["lastMessage"]["content"] == "phase6_test"


@pytest.mark.parametrize(
    "identifier,expected",
    [(15, "user_15"), ("15", "user_15"), (None, "user_null"), (True, "user_true")],
)
def test_scalar_room(identifier, expected):
    assert realtime.room(identifier) == expected


def test_no_socket_loop_retains_persistence(monkeypatch):
    monkeypatch.setattr(realtime, "_loop", None)
    assert realtime.emit("receive_message", {"id": 1}, 2, "safe-request") is None
