import subprocess
import time
from pathlib import Path

import bcrypt
import pytest
from conftest import (
    DATABASES,
    compare,
    container,
    docker,
    node_crypto,
    request_pair,
    rows,
    seed,
    select,
)

ACCOUNT = {
    "username": "fixture",
    "email": "fixture@example.invalid",
    "password": "synthetic-password",
}


@pytest.mark.parametrize("missing", ["username", "email", "password"])
def test_register_missing_fields_parity(live, missing):
    payload = dict(ACCOUNT)
    del payload[missing]
    pair = request_pair(live, "POST", "/register", payload)
    compare(pair, 400)
    assert pair["node"].json() == pair["python"].json()
    assert not rows("node") and not rows("python")


def test_register_new_account_database_effect_and_node_bcrypt_verification(live):
    pair = request_pair(live, "POST", "/register", ACCOUNT)
    compare(pair, 201)
    for kind in DATABASES:
        stored = rows(kind)
        assert len(stored) == 1 and not stored[0]["verified"]
        assert stored[0]["id"] == pair[kind].json()["userId"]
        assert stored[0]["username"] == ACCOUNT["username"]
        assert node_crypto(
            action="compare", password=ACCOUNT["password"], hash=stored[0]["password"]
        )
        assert len(stored[0]["otp"]) == 6 and stored[0]["otp"].isdigit()


@pytest.mark.parametrize(
    "field,value", [("username", "another"), ("email", "another@example.invalid")]
)
def test_verified_duplicate_username_or_email_parity(live, field, value):
    seed(node_crypto(action="hash", password=ACCOUNT["password"]))
    payload = dict(ACCOUNT)
    payload[field] = value
    pair = request_pair(live, "POST", "/register", payload)
    compare(pair, 400)
    assert pair["node"].json() == pair["python"].json()
    assert len(rows("node")) == len(rows("python")) == 1


def test_existing_unverified_account_keeps_id_and_updates_password(live):
    seed(node_crypto(action="hash", password="old-password"), verified=False)
    identifiers = {kind: rows(kind)[0]["id"] for kind in DATABASES}
    pair = request_pair(live, "POST", "/register", ACCOUNT)
    compare(pair, 201)
    for kind in DATABASES:
        stored = rows(kind)
        assert len(stored) == 1 and stored[0]["id"] == identifiers[kind]
        assert pair[kind].json()["userId"] == identifiers[kind]
        assert node_crypto(
            action="compare", password=ACCOUNT["password"], hash=stored[0]["password"]
        )


@pytest.mark.parametrize("prefix", ["2a", "2b"])
@pytest.mark.parametrize("identifier", ["username", "email"])
def test_login_legacy_hashes_and_python_token_accepted_by_node(live, prefix, identifier):
    encoded = node_crypto(action="hash", password=ACCOUNT["password"])
    encoded = "$" + prefix + encoded[3:]
    seed(encoded, verified=False)
    pair = request_pair(
        live, "POST", "/login", {identifier: ACCOUNT[identifier], "password": ACCOUNT["password"]}
    )
    compare(pair, 200)
    for kind in DATABASES:
        result = pair[kind].json()
        assert set(result) == {"token", "user"}
        assert set(result["user"]) == {"id", "username", "email", "roleId"}
        claims = node_crypto(action="verify", token=result["token"])
        assert set(claims) == {"id", "roleId", "iat", "exp"}
        assert claims["id"] == result["user"]["id"] and claims["roleId"] == 2
        assert claims["exp"] - claims["iat"] == 86400
        assert abs(claims["iat"] - time.time()) < 10
        verified = request_pair(
            live, "POST", "/verify", headers={"Authorization": "Bearer " + result["token"]}
        )
        compare(verified, 200)
        assert verified["python"].json()["user"] == claims


@pytest.mark.parametrize(
    "username,password", [("fixture", "wrong"), ("unknown", "synthetic-password")]
)
def test_invalid_login_parity(live, username, password):
    seed(node_crypto(action="hash", password=ACCOUNT["password"]))
    pair = request_pair(live, "POST", "/login", {"username": username, "password": password})
    compare(pair, 401)
    assert pair["node"].json() == pair["python"].json() == {"error": "Invalid credentials"}


def test_valid_otp_user_dependency_and_database_effect(live):
    seed(node_crypto(action="hash", password=ACCOUNT["password"]), verified=False)
    pair = request_pair(live, "POST", "/verify-otp", {"email": ACCOUNT["email"], "otp": "654321"})
    compare(pair, 200)
    assert pair["node"].json() == pair["python"].json() == {"message": "Verified successfully"}
    for kind in DATABASES:
        assert rows(kind)[0]["verified"] and rows(kind)[0]["otp"] is None
    assert int(select("user", "SELECT COUNT(*) FROM phase2_user_test.userprofiles")) >= 1


def test_invalid_otp_is_documented_divergence(live):
    seed(node_crypto(action="hash", password=ACCOUNT["password"]), verified=False)
    pair = request_pair(live, "POST", "/verify-otp", {"email": ACCOUNT["email"], "otp": "000000"})
    assert pair["node"].status_code == 500
    assert pair["python"].status_code == 400
    assert set(pair["node"].json()) == set(pair["python"].json()) == {"error"}
    assert not rows("node")[0]["verified"] and not rows("python")[0]["verified"]


def test_legacy_bypass_is_not_accepted_in_python(live):
    import re

    # Read the defect for this test only; never persist or print its secret literal.
    source = subprocess.check_output(
        [
            "git",
            "show",
            "92777b8f70b6717e3ffd12657c725b2ea4e3d0ab:"
            "auth-service/src/commands/verifyOtpHandler.js",
        ],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        encoding="utf-8",
    )
    bypass = re.search(r"otp !== '([^']+)'", source).group(1)
    seed(node_crypto(action="hash", password=ACCOUNT["password"]), verified=False)
    pair = request_pair(live, "POST", "/verify-otp", {"email": ACCOUNT["email"], "otp": bypass})
    assert pair["node"].status_code == 200
    assert pair["python"].status_code == 400
    assert not rows("python")[0]["verified"]


def test_unknown_otp_email_parity(live):
    compare(
        request_pair(
            live, "POST", "/verify-otp", {"email": "missing@example.invalid", "otp": "000000"}
        ),
        404,
    )


def test_get_user_existing_projection_and_missing_id(live):
    seed(node_crypto(action="hash", password=ACCOUNT["password"]))
    client, urls = live
    responses = {
        kind: client.get(url + "/" + str(rows(kind)[0]["id"])) for kind, url in urls.items()
    }
    compare(responses, 200)
    for response in responses.values():
        assert set(response.json()) == {"id", "username", "email", "roleId"}
        assert "password" not in response.text and "otp" not in response.text
    compare(request_pair(live, "GET", "/2147483647"), 404)


@pytest.mark.parametrize("authorization", [None, "Bearer", "Bearer invalid"])
def test_verify_missing_malformed_signature_errors(live, authorization):
    pair = request_pair(
        live, "POST", "/verify", headers={"Authorization": authorization} if authorization else {}
    )
    compare(pair, 401)
    assert pair["node"].json() == pair["python"].json()


def test_node_token_to_python_and_expiration(live):
    token = node_crypto(action="sign", claims={"id": 101, "roleId": 2})
    pair = request_pair(live, "POST", "/verify", headers={"Authorization": "Bearer " + token})
    compare(pair, 200)
    assert pair["node"].json() == pair["python"].json()
    expired = node_crypto(action="sign", claims={"id": 101, "roleId": 2}, expired=True)
    compare(
        request_pair(live, "POST", "/verify", headers={"Authorization": "Bearer " + expired}), 401
    )


def test_wrong_signature_and_non_bearer_security_divergence(live):
    import secrets

    import jwt

    wrong = jwt.encode({"id": 101, "roleId": 2}, secrets.token_urlsafe(32), algorithm="HS256")
    compare(
        request_pair(live, "POST", "/verify", headers={"Authorization": "Bearer " + wrong}), 401
    )
    valid = node_crypto(action="sign", claims={"id": 101, "roleId": 2})
    pair = request_pair(live, "POST", "/verify", headers={"Authorization": "Basic " + valid})
    assert pair["node"].status_code == 200
    assert pair["python"].status_code == 401


def test_python_bcrypt_account_authenticates_in_node(live):
    encoded = bcrypt.hashpw(ACCOUNT["password"].encode(), bcrypt.gensalt(rounds=10)).decode()
    seed(encoded)
    compare(
        request_pair(
            live, "POST", "/login", {"username": "fixture", "password": ACCOUNT["password"]}
        ),
        200,
    )


def test_node_python_long_utf8_password_truncation(live):
    password = "é" * 40
    encoded = node_crypto(action="hash", password=password)
    seed(encoded)
    compare(
        request_pair(live, "POST", "/login", {"username": "fixture", "password": password}), 200
    )
    python_hash = bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt(rounds=10)).decode()
    assert node_crypto(action="compare", password=password, hash=python_hash)


@pytest.mark.parametrize(
    "service,path,payload",
    [
        ("notification-test", "/register", ACCOUNT),
        ("user-test", "/verify-otp", {"email": ACCOUNT["email"], "otp": "654321"}),
    ],
)
def test_downstream_unavailable_preserves_success_and_persisted_state(live, service, path, payload):
    if service == "user-test":
        seed(node_crypto(action="hash", password=ACCOUNT["password"]), verified=False)
    identifier = container(service)
    docker("stop", identifier)
    try:
        pair = request_pair(live, "POST", path, payload)
        compare(pair, 201 if path == "/register" else 200)
        for kind in DATABASES:
            assert len(rows(kind)) == 1
            if path == "/verify-otp":
                assert rows(kind)[0]["verified"] and rows(kind)[0]["otp"] is None
    finally:
        docker("start", identifier)


def test_sql_guard_blocks_schema_changes(live):
    script = """
const Sequelize=require('sequelize');
const db=new Sequelize('unused','unused','unused',{dialect:'mysql',logging:false});
db.query('ALTER TABLE users ADD unsafe INT').then(()=>process.exit(1))
.catch(()=>process.stdout.write('blocked'));
"""
    # Guard throws synchronously, so wrap the invocation without touching a database.
    script = script.replace("db.query('ALTER", "Promise.resolve().then(()=>db.query('ALTER")
    script = script.replace("unsafe INT').then", "unsafe INT')).then")
    assert docker("exec", container("auth-reference"), "node", "-e", script) == "blocked"
