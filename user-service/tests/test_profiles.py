import json
import time
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import jwt
import pytest
from django.conf import settings
from django.db import OperationalError
from profiles import selectors, services
from profiles.authentication import authenticate
from profiles.exceptions import ProfileError
from profiles.models import UserProfile
from profiles.serializers import projection


@pytest.fixture
def profile():
    return UserProfile(
        id=4,
        auth_id=10,
        full_name="phase3_test_name",
        phone="phone",
        address="address",
        avatar=None,
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
        updated_at=datetime(2026, 1, 2, tzinfo=UTC),
    )


def token(**claims):
    return jwt.encode(
        {"id": 10, "roleId": 1, "exp": time.time() + 60, **claims},
        settings.JWT_SECRET,
        algorithm="HS256",
    )


def test_model_maps_legacy_identity_without_system_tables():
    assert UserProfile._meta.db_table == "userprofiles" and not UserProfile._meta.managed
    columns = {field.name: field.column for field in UserProfile._meta.fields}
    assert columns["auth_id"] == "authId" and columns["full_name"] == "fullName"
    assert columns["created_at"] == "createdAt" and columns["updated_at"] == "updatedAt"
    assert UserProfile._meta.get_field("auth_id").unique
    assert not UserProfile._meta.get_field("auth_id").is_relation


def test_projection_camelcase_null_and_exact_node_timestamp(profile):
    data = projection(profile)
    assert data == {
        "id": 4,
        "authId": 10,
        "fullName": "phase3_test_name",
        "phone": "phone",
        "address": "address",
        "avatar": None,
        "createdAt": "2026-01-02T00:00:00.000Z",
        "updatedAt": "2026-01-02T00:00:00.000Z",
    }


def test_selector_uses_auth_id_not_profile_pk(monkeypatch, profile):
    query = MagicMock()
    query.first.return_value = profile
    manager = MagicMock()
    manager.filter.return_value = query
    monkeypatch.setattr(UserProfile, "objects", manager)
    assert selectors.by_auth_id("10") is profile
    manager.filter.assert_called_once_with(auth_id=10)


@pytest.mark.parametrize("value", [None, "me", "abc", True, 1.5, 2**40])
def test_invalid_identity_does_not_query_database(value):
    assert selectors.numeric_identity(value) is None
    assert selectors.by_auth_id(value) is None


@pytest.mark.parametrize("path", ["/me", "/me/"])
def test_me_route_precedes_parameter_and_uses_token_identity(client, monkeypatch, profile, path):
    lookup = MagicMock(return_value=profile)
    monkeypatch.setattr(selectors, "by_auth_id", lookup)
    response = client.get(path, HTTP_AUTHORIZATION="Bearer " + token())
    assert response.status_code == 200 and response.json()["authId"] == 10
    lookup.assert_called_once_with(10)


def test_me_missing_profile_returns_empty_200(client, monkeypatch):
    monkeypatch.setattr(selectors, "by_auth_id", lambda _: None)
    response = client.get("/me", HTTP_AUTHORIZATION="Bearer " + token())
    assert response.status_code == 200 and response.json() == {}


def test_me_lookup_error_returns_empty_200_without_details(client, monkeypatch):
    def unavailable(_):
        raise OperationalError("sensitive profile and DB error")

    monkeypatch.setattr(selectors, "by_auth_id", unavailable)
    response = client.get("/me", HTTP_AUTHORIZATION="Bearer " + token())
    assert response.status_code == 200 and response.json() == {}


def test_public_lookup_missing_404(client, monkeypatch):
    monkeypatch.setattr(selectors, "by_auth_id", lambda _: None)
    response = client.get("/10")
    assert response.status_code == 404 and response.json() == {"error": "Profile not found"}


@pytest.mark.parametrize(
    "authorization,error",
    [(None, "Unauthorized"), ("Bearer", "Unauthorized"), ("Bearer malformed", "Invalid token")],
)
@pytest.mark.parametrize("method", ["get", "put"])
def test_jwt_missing_and_malformed_errors(client, authorization, error, method):
    kwargs = {"HTTP_AUTHORIZATION": authorization} if authorization else {}
    response = getattr(client, method)("/me", **kwargs)
    assert response.status_code == 401 and response.json() == {"error": error}


@pytest.mark.parametrize("kind", ["expired", "signature", "basic", "algorithm"])
def test_jwt_invalid_cases(client, kind):
    value = token(exp=1) if kind == "expired" else token()
    prefix = "Basic " if kind == "basic" else "Bearer "
    if kind in {"signature", "algorithm"}:
        value = jwt.encode(
            {"id": 10}, "x" * 64, algorithm="HS512" if kind == "algorithm" else "HS256"
        )
    response = client.get("/me", HTTP_AUTHORIZATION=prefix + value)
    assert response.status_code == 401 and response.json() == {"error": "Invalid token"}


def test_authentication_attaches_identity_locally():
    request = SimpleNamespace(headers={"Authorization": "Bearer " + token()})
    assert authenticate(request)["id"] == request.auth_identity["id"] == 10


def test_me_put_ignores_body_identity(client, monkeypatch, profile):
    update = MagicMock(return_value=profile)
    monkeypatch.setattr(services, "update_profile", update)
    payload = {"authId": 999, "id": 998, "fullName": "phase3_test_name"}
    response = client.put(
        "/me",
        json.dumps(payload),
        content_type="application/json",
        HTTP_AUTHORIZATION="Bearer " + token(),
    )
    assert response.status_code == 200 and response.json()["authId"] == 10
    update.assert_called_once_with(10, payload)


def test_public_put_still_allowed_without_token(client, monkeypatch, profile):
    update = MagicMock(return_value=profile)
    monkeypatch.setattr(services, "update_profile", update)
    response = client.put(
        "/10", json.dumps({"fullName": "phase3_test_name"}), content_type="application/json"
    )
    assert response.status_code == 200
    update.assert_called_once_with("10", {"fullName": "phase3_test_name"})


def test_partial_update_omitted_fields_remain_and_null_empty_are_written(monkeypatch, profile):
    manager = MagicMock()
    manager.get_or_create.return_value = profile, False
    monkeypatch.setattr(UserProfile, "objects", manager)
    profile.save = MagicMock()
    services.update_profile(
        10, {"fullName": "", "phone": None, "authId": 999, "unknown": "ignored"}
    )
    assert profile.full_name == "" and profile.phone is None and profile.address == "address"
    assert profile.auth_id == 10 and profile.id == 4
    assert set(profile.save.call_args.kwargs["update_fields"]) == {
        "full_name",
        "phone",
        "updated_at",
    }


@pytest.mark.parametrize("payload", [{}, {"fullName": "phase3_test_name"}, {"authId": 999}])
def test_noop_does_not_advance_timestamp(monkeypatch, profile, payload):
    manager = MagicMock()
    manager.get_or_create.return_value = profile, False
    monkeypatch.setattr(UserProfile, "objects", manager)
    profile.save = MagicMock()
    previous = profile.updated_at
    assert services.update_profile(10, payload) is profile
    profile.save.assert_not_called()
    assert profile.updated_at == previous


def test_create_uses_auth_id_and_only_allowed_defaults(monkeypatch, profile):
    manager = MagicMock()
    manager.get_or_create.return_value = profile, True
    monkeypatch.setattr(UserProfile, "objects", manager)
    services.update_profile("10", {"avatar": None, "id": 999, "authId": 1000})
    call = manager.get_or_create.call_args.kwargs
    assert call["auth_id"] == 10
    assert set(call["defaults"]) == {"avatar", "created_at", "updated_at"}
    assert call["defaults"]["created_at"] == call["defaults"]["updated_at"]
    result = projection(profile)
    assert result["authId"] == "10" and result["id"] == 4
    assert "avatar" in result and result["avatar"] is None
    assert not {"fullName", "phone", "address"} & set(result)


@pytest.mark.parametrize("payload", [[1], {"fullName": {}}, {"phone": 123}])
def test_invalid_profile_types_controlled(payload):
    with pytest.raises(ProfileError):
        services.update_profile(10, payload)


def test_public_update_database_error_hides_details(client, monkeypatch):
    def fail(*_):
        raise OperationalError("password and sensitive DB details")

    monkeypatch.setattr(services, "update_profile", fail)
    response = client.put("/10", "{}", content_type="application/json")
    assert response.status_code == 500 and response.json() == {"error": "Internal Server Error"}
