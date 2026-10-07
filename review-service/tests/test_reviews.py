from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from reviews import services, storage
from reviews.exceptions import LegacyError
from reviews.models import Review
from reviews.serializers import response, truthy


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, False),
        ("", False),
        (0, False),
        (False, False),
        ("0", True),
        ("false", True),
        (1, True),
        ([], True),
        ({}, True),
    ],
)
def test_js_truthy(value, expected):
    assert truthy(value) == expected


@pytest.mark.parametrize("rating", [1, "1", 5, "5", 3])
def test_valid_rating(rating):
    assert services.rating_value(rating) == int(rating)


@pytest.mark.parametrize("rating", [0, 6, "invalid", None])
def test_invalid_rating_stays_500(rating):
    with pytest.raises(LegacyError) as error:
        services.rating_value(rating)
    assert error.value.status == 500


def test_runtime_mapping():
    assert Review._meta.db_table == "reviews" and not Review._meta.managed
    assert Review._meta.get_field("imageUrl").column == "imageUrl"
    assert Review._meta.get_field("postId").null
    assert not any(field.is_relation for field in Review._meta.fields)


def test_create_vs_query_types_and_omission():
    data = dict(
        id=1,
        reviewerId=2,
        revieweeId=3,
        postId=None,
        rating=4,
        comment=None,
        imageUrl=None,
        createdAt=datetime(2026, 1, 1, tzinfo=UTC),
        updatedAt=datetime(2026, 1, 1, tzinfo=UTC),
    )
    row = SimpleNamespace(**data)
    raw = response(row, {"reviewerId": "2", "revieweeId": "3", "rating": "4"}, create=True)
    assert (
        raw["rating"] == "4"
        and "comment" not in raw
        and "postId" not in raw
        and raw["imageUrl"] is None
    )
    assert response(row)["rating"] == 4 and response(row)["postId"] is None


def test_wrong_field_and_too_many_public(client):
    for files in (
        {"images": SimpleUploadedFile("x.png", b"x")},
        {"image": [SimpleUploadedFile("x.png", b"x"), SimpleUploadedFile("y.png", b"y")]},
    ):
        result = client.post("/", files)
        assert result.status_code == 500 and result.json() == {"error": "Unexpected field"}


def test_safe_save_collision_and_bytes(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_ROOT", tmp_path)
    monkeypatch.setattr(storage.time, "time", lambda: 10)
    old = tmp_path / "10000-a.bin"
    old.write_bytes(b"old")
    paths = storage.save_files([SimpleUploadedFile("a.bin", b"new\x00")])
    assert (
        paths[0].name == "10001-a.bin"
        and old.read_bytes() == b"old"
        and paths[0].read_bytes() == b"new\x00"
    )


def test_unlink_blocks_unsafe_and_shared_review(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_ROOT", tmp_path)
    target = tmp_path / "x.bin"
    target.write_bytes(b"preserve")
    query = MagicMock()
    query.exclude.return_value.exists.return_value = True
    monkeypatch.setattr(Review.objects, "filter", lambda **kwargs: query)
    storage.unlink_image("/uploads/x.bin", 1, "safe")
    storage.unlink_image("/uploads/../x.bin", 1, "safe")
    assert target.read_bytes() == b"preserve"


@pytest.mark.parametrize("mode", ["owned", "post-shared", "unavailable"])
def test_unlink_requires_post_ownership_check(tmp_path, monkeypatch, mode):
    import httpx

    monkeypatch.setattr(settings, "UPLOAD_ROOT", tmp_path)
    settings.SERVICE_URLS["POST_SERVICE_URL"] = "http://post.test"
    target = tmp_path / "x.bin"
    target.write_bytes(b"preserve")
    query = MagicMock()
    query.exclude.return_value.exists.return_value = False
    monkeypatch.setattr(Review.objects, "filter", lambda **kwargs: query)

    def fetch(*args, **kwargs):
        assert kwargs["headers"] == {"X-Request-ID": "safe"}
        if mode == "unavailable":
            raise httpx.ConnectError("private")
        return httpx.Response(
            200,
            json=[{"Images": [{"imageUrl": "/uploads/x.bin"}]}] if mode == "post-shared" else [],
            request=httpx.Request("GET", "http://post.test"),
        )

    monkeypatch.setattr(httpx, "get", fetch)
    storage.unlink_image("/uploads/x.bin", 1, "safe")
    assert target.exists() == (mode != "owned")


def test_failed_insert_cleans_only_new_file(tmp_path, monkeypatch):
    from contextlib import nullcontext

    from django.db import IntegrityError

    monkeypatch.setattr(settings, "UPLOAD_ROOT", tmp_path)
    old = tmp_path / "legacy.bin"
    old.write_bytes(b"legacy")
    monkeypatch.setattr(services.transaction, "atomic", nullcontext)

    def fail(**kwargs):
        raise IntegrityError("private DB details")

    monkeypatch.setattr(Review.objects, "create", fail)
    with pytest.raises(IntegrityError):
        services.create(
            {"reviewerId": 1, "revieweeId": 2, "rating": 4}, SimpleUploadedFile("unit.bin", b"new")
        )
    assert list(tmp_path.iterdir()) == [old] and old.read_bytes() == b"legacy"


def test_committed_replacement_survives_unlink_failure(tmp_path, monkeypatch):
    from contextlib import nullcontext
    from datetime import UTC, datetime

    monkeypatch.setattr(settings, "UPLOAD_ROOT", tmp_path)
    row = Review(
        id=1,
        reviewerId=1,
        revieweeId=2,
        rating=4,
        imageUrl="/uploads/old.bin",
        createdAt=datetime(2026, 1, 1, tzinfo=UTC),
        updatedAt=datetime(2026, 1, 1, tzinfo=UTC),
    )
    row.save = MagicMock()
    query = MagicMock()
    query.extra.return_value.first.return_value = row
    monkeypatch.setattr(Review.objects, "select_for_update", lambda: query)
    monkeypatch.setattr(services.transaction, "atomic", nullcontext)

    def fail(*args):
        raise OSError("private file details")

    monkeypatch.setattr(storage, "unlink_image", fail)
    result = services.update(1, {}, SimpleUploadedFile("unit.bin", b"new"), "unit")
    assert (tmp_path / result["imageUrl"].removeprefix("/uploads/")).read_bytes() == b"new"
    row.save.assert_called_once()
