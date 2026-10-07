from types import SimpleNamespace
from unittest.mock import MagicMock

import jwt
import pytest
from authentication import selectors
from authentication.models import AuthUser
from authentication.services import clients, passwords, tokens
from django.conf import settings
from django.db import OperationalError


@pytest.fixture
def account(monkeypatch):
    user = SimpleNamespace(
        id=101,
        role_id=1,
        username="synthetic",
        email="synthetic@example.invalid",
        password=passwords.hash_password("synthetic-password"),
        is_verified=False,
        otp="654321",
        save=MagicMock(),
    )
    monkeypatch.setattr(selectors, "by_identifier", lambda _: user)
    monkeypatch.setattr(selectors, "for_registration", lambda *_: user)
    monkeypatch.setattr(selectors, "by_email", lambda _: user)
    monkeypatch.setattr(selectors, "by_id", lambda _: user)
    monkeypatch.setattr(clients, "send_otp_email", MagicMock())
    monkeypatch.setattr(clients, "create_profile", MagicMock())
    return user


def test_explicit_model_mapping():
    assert AuthUser._meta.db_table == "users"
    assert AuthUser._meta.managed is False
    assert AuthUser._meta.get_field("role_id").column == "roleId"
    assert AuthUser._meta.get_field("created_at").column == "createdAt"
    assert AuthUser._meta.get_field("username").unique
    assert AuthUser._meta.get_field("email").unique


@pytest.mark.parametrize("missing", ["username", "email", "password"])
def test_registration_validation(client, missing):
    data = {"username": "synthetic", "email": "test@example.invalid", "password": "test"}
    del data[missing]
    response = client.post("/register", data=data)
    assert response.status_code == 400
    assert response.json() == {"message": "Vui lòng điền đầy đủ thông tin"}


def test_unverified_registration_updates_same_account(client, account):
    response = client.post(
        "/register",
        data={
            "username": "new-synthetic",
            "email": "new@example.invalid",
            "password": "changed",
        },
    )
    assert response.status_code == 201 and response.json()["userId"] == 101
    assert account.username == "new-synthetic"
    assert passwords.verify_password("changed", account.password)
    assert len(account.otp) == 6 and account.otp.isdigit()
    account.save.assert_called_once()
    clients.send_otp_email.assert_called_once()


def test_new_registration_and_timestamp_fields(client, account, monkeypatch):
    monkeypatch.setattr(selectors, "for_registration", lambda *_: None)
    create = MagicMock(return_value=account)
    monkeypatch.setattr(AuthUser.objects, "create", create)
    response = client.post(
        "/register",
        data={
            "username": "synthetic",
            "email": "test@example.invalid",
            "password": "test",
        },
    )
    assert response.status_code == 201
    values = create.call_args.kwargs
    assert values["created_at"] == values["updated_at"]
    assert passwords.verify_password("test", values["password"])


@pytest.mark.parametrize(
    "username,email,message",
    [
        ("synthetic", "other@example.invalid", "Tên đăng nhập đã tồn tại"),
        ("other", "synthetic@example.invalid", "Email đã được sử dụng"),
    ],
)
def test_verified_duplicates(client, account, username, email, message):
    account.is_verified = True
    response = client.post(
        "/register", data={"username": username, "email": email, "password": "x"}
    )
    assert response.status_code == 400 and response.json() == {"message": message}
    account.save.assert_not_called()


@pytest.mark.parametrize("identifier", ["username", "email"])
def test_login_projection_claims_and_unverified_parity(client, account, identifier):
    response = client.post(
        "/login", data={identifier: getattr(account, identifier), "password": "synthetic-password"}
    )
    assert response.status_code == 200
    result = response.json()
    assert set(result) == {"token", "user"}
    assert result["user"] == {
        "id": 101,
        "username": "synthetic",
        "email": "synthetic@example.invalid",
        "roleId": 1,
    }
    claims = jwt.decode(result["token"], settings.JWT_SECRET, algorithms=["HS256"])
    assert set(claims) == {"id", "roleId", "iat", "exp"}
    assert claims["exp"] - claims["iat"] == 86400
    account.save.assert_not_called()


def test_wrong_password_and_unknown_account(client, account, monkeypatch):
    assert (
        client.post("/login", data={"username": "synthetic", "password": "wrong"}).status_code
        == 401
    )
    monkeypatch.setattr(selectors, "by_identifier", lambda _: None)
    assert client.post("/login", data={"username": "unknown", "password": "x"}).json() == {
        "error": "Invalid credentials"
    }


def test_valid_otp_saves_before_profile(client, account):
    response = client.post("/verify-otp", data={"email": account.email, "otp": account.otp})
    assert response.status_code == 200 and response.json() == {"message": "Verified successfully"}
    assert account.is_verified and account.otp is None
    account.save.assert_called_once()
    clients.create_profile.assert_called_once()


def test_wrong_empty_and_replayed_otp_never_save(client, account):
    for otp in ["000000", "", None]:
        response = client.post(
            "/verify-otp",
            data={"email": account.email, "otp": otp},
            content_type="application/json",
        )
        assert response.status_code == 400
    account.otp = None
    assert (
        client.post("/verify-otp", data={"email": account.email, "otp": "654321"}).status_code
        == 400
    )
    account.save.assert_not_called()


def test_unknown_email_and_id(client, account, monkeypatch):
    monkeypatch.setattr(selectors, "by_email", lambda _: None)
    monkeypatch.setattr(selectors, "by_id", lambda _: None)
    assert client.post("/verify-otp", data={"email": "none", "otp": "654321"}).status_code == 404
    assert client.get("/999999").json() == {"error": "User not found"}


def test_user_projection_contains_no_secrets(client, account):
    response = client.get("/101")
    assert set(response.json()) == {"id", "username", "email", "roleId"}


@pytest.mark.parametrize(
    "authorization", [None, "Bearer", "Basic invalid", "Bearer invalid", "Bearer a b"]
)
def test_token_errors(client, authorization):
    headers = {"HTTP_AUTHORIZATION": authorization} if authorization else {}
    response = client.post("/verify", **headers)
    assert response.status_code == 401 and set(response.json()) == {"error"}


def test_token_valid_expired_and_wrong_key(client, account):
    assert client.post(
        "/verify", HTTP_AUTHORIZATION="Bearer " + tokens.issue_token(account)
    ).json()["valid"]
    for claims, key in [
        ({"id": 101, "exp": 1}, settings.JWT_SECRET),
        ({"id": 101}, "synthetic-wrong-key-which-is-long-enough"),
    ]:
        token = jwt.encode(claims, key, algorithm="HS256")
        assert client.post("/verify", HTTP_AUTHORIZATION="Bearer " + token).status_code == 401


@pytest.mark.parametrize("prefix", [b"2a", b"2b"])
def test_bcrypt_legacy_prefixes_and_truncation(prefix):
    encoded = passwords.hash_password("é" * 40)
    encoded = "$" + prefix.decode() + encoded[3:]
    assert passwords.verify_password("é" * 40, encoded)
    assert passwords.verify_password("é" * 36 + "different suffix", encoded)
    assert not passwords.verify_password("wrong", encoded)


def test_database_exception_does_not_leak(client, monkeypatch):
    def fail(_):
        raise OperationalError("password=secret")

    monkeypatch.setattr(selectors, "by_id", fail)
    response = client.get("/101")
    assert response.status_code == 500 and response.json() == {"error": "Internal Server Error"}
