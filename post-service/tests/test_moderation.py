from contextlib import nullcontext
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import jwt
import pytest
from django.conf import settings
from posts import clients, services, storage
from posts.models import Image, Post


def record(status="pending"):
    return Post(
        id=17,
        userId=18,
        categoryId=1,
        title="Moderation test",
        price=Decimal("1.00"),
        status=status,
        createdAt=datetime(2026, 1, 1, tzinfo=UTC),
        updatedAt=datetime(2026, 1, 1, tzinfo=UTC),
    )


def dependencies(monkeypatch, row):
    monkeypatch.setattr(services.transaction, "atomic", nullcontext)
    manager = Mock()
    query = manager.select_for_update.return_value.prefetch_related.return_value
    query.filter.return_value.first.return_value = row
    monkeypatch.setattr(Post, "objects", manager)
    monkeypatch.setattr(type(row.Images), "all", lambda _: [])
    row.save = Mock()
    monkeypatch.setattr(clients, "categories", Mock(return_value={}))
    sync = Mock()
    notify = Mock()
    monkeypatch.setattr(clients, "sync_search", sync)
    monkeypatch.setattr(clients, "notify", notify)
    return sync, notify


def test_create_cannot_override_pending_with_client_status(monkeypatch):
    manager = Mock()
    manager.create.side_effect = lambda **kwargs: Post(id=17, **kwargs)
    monkeypatch.setattr(Post, "objects", manager)
    images = Mock()
    images.bulk_create.return_value = []
    monkeypatch.setattr(Image, "objects", images)
    monkeypatch.setattr(services.transaction, "atomic", nullcontext)
    monkeypatch.setattr(storage, "save_files", lambda _: [])
    monkeypatch.setattr(clients, "categories", lambda _: {})
    sync = Mock()
    monkeypatch.setattr(clients, "sync_search", sync)
    result = services.create(
        18, {"title": "test", "price": "1.00", "categoryId": 1, "status": "approved"}, [], "test-id"
    )
    assert result["status"] == "pending"
    assert sync.call_args.args[0]["status"] == "pending"


@pytest.mark.parametrize("status", ["approved", "rejected"])
def test_pending_decision_persists_and_syncs(monkeypatch, status):
    row = record()
    sync, notify = dependencies(monkeypatch, row)
    result = services.moderate(17, {"status": status}, "test-id")
    assert row.status == result["status"] == status
    row.save.assert_called_once_with(update_fields=["status", "updatedAt"])
    assert sync.call_args.args[0]["status"] == status
    notify.assert_called_once_with(row, "test-id")


@pytest.mark.parametrize("status", ["approved", "rejected"])
def test_repeat_decision_does_not_duplicate_notification(monkeypatch, status):
    row = record(status)
    sync, notify = dependencies(monkeypatch, row)
    services.moderate(17, {"status": status}, "test-id")
    row.save.assert_not_called()
    notify.assert_not_called()
    sync.assert_called_once()


@pytest.mark.parametrize(
    "body",
    [{}]
    + [
        {"status": value}
        for value in ["available", "pending", "deleted", "custom", "", None, [], {}, 1]
    ],
)
def test_invalid_decision_returns_400_without_writes(client, monkeypatch, body):
    manager = Mock()
    sync, notify = Mock(), Mock()
    monkeypatch.setattr(Post, "objects", manager)
    monkeypatch.setattr(clients, "sync_search", sync)
    monkeypatch.setattr(clients, "notify", notify)
    token = jwt.encode({"id": 18, "roleId": 2}, settings.JWT_SECRET, algorithm="HS256")
    response = client.put(
        "/admin/posts/17",
        data=body,
        content_type="application/json",
        HTTP_AUTHORIZATION="Bearer " + token,
    )
    assert response.status_code == 400
    assert response.json() == {"error": "Status must be approved or rejected"}
    manager.select_for_update.assert_not_called()
    sync.assert_not_called()
    notify.assert_not_called()
