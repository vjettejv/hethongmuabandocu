import json
from contextlib import nullcontext
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import jwt
import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import RequestFactory, override_settings
from posts import clients, selectors, services, storage
from posts.models import Image, Post
from posts.serializers import formatted_response, raw_response

NOW = datetime(2026, 1, 2, tzinfo=UTC)


def post():
    return Post(
        id=7,
        userId=8,
        categoryId=9,
        title="Tiêu đề",
        price=Decimal("12.50"),
        createdAt=NOW,
        updatedAt=NOW,
    )


def token(**claims):
    return jwt.encode({"id": 8, "roleId": 1, **claims}, settings.JWT_SECRET, algorithm="HS256")


def test_models_match_existing_tables():
    assert Post._meta.managed is Image._meta.managed is False
    assert Post._meta.db_table == "posts" and Image._meta.db_table == "images"
    assert Post._meta.pk.get_internal_type() == "AutoField"
    assert not any(field.is_relation for field in Post._meta.fields)
    assert Image._meta.get_field("post").column == "postId"
    for name in ("userId", "categoryId", "createdAt", "updatedAt"):
        assert Post._meta.get_field(name).column == name


def test_endpoint_specific_price_and_images(monkeypatch):
    record = post()
    image = Image(id=1, post=record, imageUrl="/uploads/example", createdAt=NOW, updatedAt=NOW)
    monkeypatch.setattr(type(record.Images), "all", lambda _: [image])
    formatted = formatted_response(record, {})
    assert formatted["price"] == 12.5 and isinstance(formatted["price"], float)
    assert formatted["Category"] == {"id": 9, "name": "Đang cập nhật"}
    assert formatted["Images"][0]["postId"] == 7
    created = raw_response(record, original={"categoryId": "9", "price": "12.50"})
    assert created["categoryId"] == "9" and created["price"] == "12.50"
    assert not {"Images", "Category", "description", "condition"} & set(created)
    admin = raw_response(record, images=[image])
    assert admin["price"] == "12.50" and "Category" not in admin
    assert admin["createdAt"] == "2026-01-02T00:00:00.000Z"


@pytest.mark.parametrize(
    "path,method",
    [
        ("/my-posts", "get"),
        ("/", "post"),
        ("/1", "delete"),
        ("/admin/posts", "get"),
        ("/admin/posts/1", "put"),
        ("/admin/posts/1", "delete"),
    ],
)
@pytest.mark.parametrize(
    "authorization,error", [("", "Unauthorized"), ("Bearer bad", "Invalid token")]
)
def test_protected_routes(client, path, method, authorization, error):
    response = getattr(client, method)(path, HTTP_AUTHORIZATION=authorization)
    assert response.status_code == 401 and response.json() == {"error": error}


@pytest.mark.parametrize("authorization", ["Basic ", "Bearer ", "Bearer invalid extra"])
def test_malformed_authorization(client, authorization):
    assert client.get("/my-posts", HTTP_AUTHORIZATION=authorization).status_code == 401


def test_valid_jwt_route_order_and_no_role_check(client, monkeypatch):
    seen = []
    monkeypatch.setattr(selectors, "list_posts", lambda *args, **kw: seen.append(kw) or [])
    monkeypatch.setattr(clients, "categories", lambda _: {})
    headers = {"HTTP_AUTHORIZATION": "Bearer " + token()}
    assert client.get("/my-posts", **headers).json() == []
    assert seen == [{"user_id": 8}]
    assert client.get("/admin/posts", **headers).json() == {"data": []}


def test_expired_and_wrong_signature(client):
    expired = token(exp=1)
    wrong = jwt.encode({"id": 8}, "different-key-for-phase4-test-123456789", algorithm="HS256")
    for value in (expired, wrong):
        assert client.get("/my-posts", HTTP_AUTHORIZATION="Bearer " + value).json() == {
            "error": "Invalid token"
        }


def test_like_wildcards_remain_parameterized(monkeypatch):
    manager = Mock()
    manager.all.return_value = manager
    manager.extra.return_value = manager
    manager.order_by.return_value = manager
    manager.values.return_value = []
    monkeypatch.setattr(Post, "objects", manager)
    selectors.list_posts({"keyword": "x%_' OR 1=1"})
    manager.extra.assert_called_once_with(
        where=["`posts`.`title` LIKE %s"], params=["%x%_' OR 1=1%"]
    )


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("ph%beta", "ph%beta"),
        ("ph%25beta", "ph%beta"),
        ("test+name", "test name"),
        ("caf%C3%A9", "café"),
    ],
)
def test_express_query_decode_fallback(raw, expected):
    request = SimpleNamespace(
        query_params=SimpleNamespace(dict=lambda: {}), META={"QUERY_STRING": "keyword=" + raw}
    )
    assert selectors.legacy_parameters(request)["keyword"] == expected


@pytest.mark.parametrize("count", [1, 5])
def test_storage_bytes_and_timestamp_basename(tmp_path, count):
    uploads = [SimpleUploadedFile(f"photo{i}.bin", bytes(range(256))) for i in range(count)]
    with override_settings(UPLOAD_ROOT=tmp_path):
        paths = storage.save_files(uploads)
    assert len(paths) == count
    assert all(path.read_bytes() == bytes(range(256)) for path in paths)
    assert all(path.name.split("-", 1)[0].isdigit() for path in paths)


def test_collision_preserves_existing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(storage.time, "time", lambda: 1)
    existing = tmp_path / "1000-photo.bin"
    existing.write_bytes(b"existing")
    with override_settings(UPLOAD_ROOT=tmp_path):
        created = storage.save_files([SimpleUploadedFile("photo.bin", b"new")])
    assert created[0].name == "1001-photo.bin" and existing.read_bytes() == b"existing"


def test_storage_failure_removes_only_owned_files(tmp_path):
    existing = tmp_path / "old.bin"
    existing.write_bytes(b"keep")
    bad = Mock(name="bad")
    bad.name = "broken.bin"
    bad.chunks.side_effect = OSError("synthetic failure")
    with override_settings(UPLOAD_ROOT=tmp_path), pytest.raises(OSError):
        storage.save_files([SimpleUploadedFile("good.bin", b"first"), bad])
    assert list(tmp_path.iterdir()) == [existing]


def test_database_failure_removes_operation_files(tmp_path, monkeypatch):
    monkeypatch.setattr(services.transaction, "atomic", nullcontext)
    manager = Mock()
    manager.create.side_effect = IntegrityError("sensitive SQL")
    monkeypatch.setattr(Post, "objects", manager)
    with override_settings(UPLOAD_ROOT=tmp_path), pytest.raises(IntegrityError):
        services.create(
            8,
            {"title": "test", "categoryId": 1, "price": "1"},
            [SimpleUploadedFile("new.bin", b"data")],
            "safe-id",
        )
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("name", ["../old.bin", ".hidden", "sub/../../old.bin"])
def test_static_rejects_escape_and_dotfiles(tmp_path, name):
    with override_settings(UPLOAD_ROOT=tmp_path):
        assert storage.serve(RequestFactory().get("/"), name).status_code == 404


def test_static_symlink_cannot_escape(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.write_bytes(b"private")
    # Windows Developer Mode/admin may be needed; use a mocked resolved path, no skip.
    original = storage.Path.resolve

    def resolve(path):
        return outside if path.name == "link" else original(path)

    with override_settings(UPLOAD_ROOT=root), pytest.MonkeyPatch.context() as patch:
        patch.setattr(storage.Path, "resolve", resolve)
        assert storage.serve(RequestFactory().get("/"), "link").status_code == 404


@pytest.mark.parametrize(
    "method,range_header,status,body",
    [
        ("get", "", 200, b"0123456789"),
        ("head", "", 200, b""),
        ("get", "bytes=2-5", 206, b"2345"),
        ("get", "bytes=-3", 206, b"789"),
        ("get", "bytes=99-", 416, b""),
    ],
)
def test_binary_static_and_ranges(tmp_path, method, range_header, status, body):
    (tmp_path / "sample.bin").write_bytes(b"0123456789")
    request = getattr(RequestFactory(), method)("/", HTTP_RANGE=range_header)
    with override_settings(UPLOAD_ROOT=tmp_path):
        response = storage.serve(request, "sample.bin")
        actual = b"".join(response.streaming_content) if response.streaming else response.content
        response.close()
    assert response.status_code == status and actual == body


def test_static_conditional_request(tmp_path):
    (tmp_path / "test.bin").write_bytes(b"data")
    with override_settings(UPLOAD_ROOT=tmp_path):
        first = storage.serve(RequestFactory().head("/"), "test.bin")
        cached = storage.serve(
            RequestFactory().get("/", HTTP_IF_NONE_MATCH=first["ETag"]), "test.bin"
        )
    assert cached.status_code == 304


@pytest.mark.parametrize("mode", ["timeout", "bad_json", "failure"])
def test_dependency_failure_is_controlled(monkeypatch, mode, caplog):
    response = httpx.Response(
        503 if mode == "failure" else 200, content=b"bad" if mode == "bad_json" else b"{}"
    )
    transport = Mock()
    transport.__enter__ = Mock(return_value=transport)
    transport.__exit__ = Mock(return_value=False)
    if mode == "timeout":
        transport.request.side_effect = httpx.ConnectTimeout("secret-url")
    else:
        transport.request.return_value = response
    monkeypatch.setattr(clients.httpx, "Client", lambda **_: transport)
    with override_settings(SERVICE_URLS={"CATEGORY_SERVICE_URL": "http://synthetic"}):
        assert clients.categories("safe-request") == {}
    assert "secret-url" not in caplog.text


def test_search_payload_omits_undefined_description_and_forwards_id(monkeypatch):
    dispatch = Mock()
    monkeypatch.setattr(clients, "dispatch", dispatch)
    raw = raw_response(post(), original={"categoryId": "9", "price": "12.50"})
    clients.sync_search(
        raw, {"9": {"name": "Danh mục"}}, "safe-id", [{"imageUrl": "/uploads/test"}]
    )
    dispatch.assert_called_once_with(
        "SEARCH",
        "/sync",
        {
            "postId": 7,
            "title": "Tiêu đề",
            "price": "12.50",
            "categoryId": "9",
            "status": "pending",
            "imageUrl": "/uploads/test",
            "categoryName": "Danh mục",
        },
        "safe-id",
    )


def test_dependency_logs_contain_only_metadata():
    import logging

    from common.logging import JsonFormatter

    record = logging.LogRecord(
        "posts.dependencies", logging.WARNING, __file__, 1, "sensitive-url-and-body", (), None
    )
    record.dependency = "SEARCH"
    record.failure = "http_status"
    data = json.loads(JsonFormatter("post-service").format(record))
    assert data["dependency"] == "SEARCH" and "sensitive" not in json.dumps(data)


def test_capacity_drop_is_best_effort(monkeypatch):
    slots = Mock()
    slots.acquire.return_value = False
    monkeypatch.setattr(clients, "SLOTS", slots)
    executor = Mock()
    monkeypatch.setattr(clients, "EXECUTOR", executor)
    clients.dispatch("SEARCH", "/sync", {}, "safe-id")
    executor.submit.assert_not_called()


def test_safe_unexpected_error_envelope(client, monkeypatch):
    monkeypatch.setattr(selectors, "detail", Mock(side_effect=IntegrityError("password SQL")))
    response = client.get("/123")
    assert response.status_code == 500 and response.json() == {"error": "Internal Server Error"}


def test_admin_delete_does_not_dispatch(monkeypatch):
    monkeypatch.setattr(services.transaction, "atomic", nullcontext)
    monkeypatch.setattr(Image, "objects", Mock())
    monkeypatch.setattr(Post, "objects", Mock())
    dispatch = Mock()
    monkeypatch.setattr(clients, "dispatch", dispatch)
    assert services.admin_delete(7) == {"message": "Deleted"}
    dispatch.assert_not_called()


def test_category_fetched_once_for_list(client, monkeypatch):
    records = [SimpleNamespace() for _ in range(10)]
    monkeypatch.setattr(selectors, "list_posts", lambda _: records)
    fetch = Mock(return_value={})
    monkeypatch.setattr(clients, "categories", fetch)
    monkeypatch.setattr("posts.views.formatted_response", lambda post, categories: {})
    assert len(client.get("/").json()) == 10
    fetch.assert_called_once()
