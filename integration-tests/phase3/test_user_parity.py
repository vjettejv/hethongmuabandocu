import secrets

import jwt
import pytest
from conftest import (
    AUTH_ID,
    compare,
    compare_records,
    node_token,
    pair,
    profile_rows,
    seed_profiles,
)


@pytest.mark.parametrize("path", [f"/{AUTH_ID}", f"/{AUTH_ID}/", "/me", "/me/"])
def test_existing_profile_identity_camelcase_and_timestamp_parity(live, path):
    seed_profiles()
    responses = pair(live, "user", "GET", path, headers={"Authorization": "Bearer " + node_token()})
    compare(responses, 200)
    compare_records(responses["node"].json(), responses["python"].json())
    for response in responses.values():
        assert response.json()["id"] == 4 and response.json()["authId"] == AUTH_ID
    missing_pk = pair(live, "user", "GET", "/4")
    compare(missing_pk, 404)


@pytest.mark.parametrize(
    "path,status,body", [("/me", 200, {}), (f"/{AUTH_ID}", 404, {"error": "Profile not found"})]
)
def test_missing_profile_parity(live, path, status, body):
    responses = pair(live, "user", "GET", path, headers={"Authorization": "Bearer " + node_token()})
    compare(responses, status)
    assert responses["node"].json() == responses["python"].json() == body


@pytest.mark.parametrize(
    "authorization,error",
    [(None, "Unauthorized"), ("Bearer", "Unauthorized"), ("Bearer invalid", "Invalid token")],
)
@pytest.mark.parametrize("method", ["GET", "PUT"])
def test_authorization_errors_parity(live, authorization, error, method):
    headers = {"Authorization": authorization} if authorization else {}
    responses = pair(live, "user", method, "/me", payload={}, headers=headers)
    compare(responses, 401)
    assert responses["node"].json() == responses["python"].json() == {"error": error}


@pytest.mark.parametrize("kind", ["expired", "signature"])
def test_expired_and_wrong_signature_parity(live, kind):
    value = (
        node_token(expired=True)
        if kind == "expired"
        else jwt.encode({"id": AUTH_ID}, secrets.token_urlsafe(48), algorithm="HS256")
    )
    responses = pair(live, "user", "GET", "/me", headers={"Authorization": "Bearer " + value})
    compare(responses, 401)
    assert responses["node"].json() == responses["python"].json() == {"error": "Invalid token"}


@pytest.mark.parametrize("path", [f"/{AUTH_ID}", "/me"])
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"fullName": "phase3_test_Đồ cũ", "phone": ""},
        {"fullName": None, "avatar": None},
        {"authId": 999, "id": 998, "unknown": "ignored"},
    ],
)
def test_put_find_or_create_and_body_identity_not_override(live, path, payload):
    responses = pair(
        live,
        "user",
        "PUT",
        path,
        payload=payload,
        headers={"Authorization": "Bearer " + node_token()},
    )
    compare(responses, 200)
    compare_records(responses["node"].json(), responses["python"].json(), generated=True)
    for kind, response in responses.items():
        result = response.json()
        assert result["authId"] == (AUTH_ID if path == "/me" else str(AUTH_ID))
        assert result["id"] != AUTH_ID
        for field in ["fullName", "phone", "address", "avatar"]:
            if field in payload:
                assert result[field] == payload[field]
            else:
                assert field not in result
        stored = profile_rows(kind)
        assert len(stored) == 1 and stored[0]["authId"] == AUTH_ID
        assert stored[0]["fullName"] == result.get("fullName")
        retrieved = live[0].get(live[1]["user"][kind] + f"/{AUTH_ID}")
        assert retrieved.status_code == 200 and retrieved.json()["authId"] == AUTH_ID
        assert retrieved.json()["address"] is None
        assert retrieved.json()["fullName"] == payload.get("fullName")


@pytest.mark.parametrize(
    "payload",
    [{}, {"fullName": "phase3_test_name"}, {"phone": None, "avatar": ""}, {"fullName": "new"}],
)
def test_partial_update_null_empty_noop_and_stable_created_at(live, payload):
    seed_profiles()
    responses = pair(live, "user", "PUT", f"/{AUTH_ID}", payload=payload)
    compare(responses, 200)
    compare_records(responses["node"].json(), responses["python"].json(), generated=True)
    for kind, response in responses.items():
        result = response.json()
        assert result["createdAt"] == "2026-01-02T00:00:00.000Z"
        assert result["address"] == "address"
        assert result["phone"] == payload.get("phone", "phone")
        assert result["avatar"] == payload.get("avatar")
        if payload in ({}, {"fullName": "phase3_test_name"}):
            assert result["updatedAt"] == result["createdAt"]
        stored = profile_rows(kind)
        assert stored[0]["id"] == 4 and stored[0]["fullName"] == result["fullName"]


def test_strict_bearer_is_documented_divergence(live):
    seed_profiles()
    responses = pair(live, "user", "GET", "/me", headers={"Authorization": "Basic " + node_token()})
    assert responses["node"].status_code == 200 and responses["python"].status_code == 401


def test_gateway_all_four_user_routes(live):
    client, urls = live
    headers = {"Authorization": "Bearer " + node_token(), "X-Request-ID": "phase3-profile"}
    for path in [f"/users/{AUTH_ID}", "/users/me"]:
        response = client.put(
            urls["gateway"] + path, json={"fullName": "phase3_test_name"}, headers=headers
        )
        assert response.status_code == 200 and int(response.json()["authId"]) == AUTH_ID
        assert response.headers["x-request-id"] == "phase3-profile"
        retrieved = client.get(urls["gateway"] + path, headers=headers)
        assert retrieved.status_code == 200 and retrieved.json()["fullName"] == "phase3_test_name"
