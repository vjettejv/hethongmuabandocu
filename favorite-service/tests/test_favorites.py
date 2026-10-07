import time
from unittest.mock import MagicMock

import jwt
import pytest
from django.conf import settings
from favorites import clients, selectors, services
from favorites.models import Favorite


@pytest.mark.parametrize(
    "method,path", [("post", "/toggle"), ("get", "/check/1"), ("get", "/my-favorites")]
)
@pytest.mark.parametrize("kind", ["missing", "invalid", "expired", "wrong"])
def test_jwt_failures(client, method, path, kind):
    token = jwt.encode(
        {"id": 12, "exp": time.time() + (-10 if kind == "expired" else 30)},
        "wrong-key-with-at-least-32-characters" if kind == "wrong" else settings.JWT_SECRET,
        algorithm="HS256",
    )
    header = (
        {}
        if kind == "missing"
        else {"HTTP_AUTHORIZATION": "Bearer " + ("invalid" if kind == "invalid" else token)}
    )
    result = getattr(client, method)(
        path, data={"postId": 1}, content_type="application/json", **header
    )
    assert result.status_code == 401
    assert result.json() == {"error": "Unauthorized" if kind == "missing" else "Invalid token"}


def test_identity_and_legacy_toggle(client, monkeypatch):
    capture = []
    monkeypatch.setattr(
        services,
        "toggle",
        lambda user, data: (
            capture.append((user, data)) or {"message": "Added to favorites", "isFavorited": True}
        ),
    )
    token = jwt.encode({"id": 42, "roleId": 1}, settings.JWT_SECRET, algorithm="HS256")
    result = client.post(
        "/toggle/",
        data={"postId": 9, "userId": 999},
        content_type="application/json",
        HTTP_AUTHORIZATION="Bearer " + token,
    )
    assert result.status_code == 201 and capture[0][0] == 42
    assert result.json() == {"message": "Added to favorites", "isFavorited": True}


def test_no_extra_delete(client):
    assert client.delete("/9").status_code == 404


def test_local_legacy_mapping():
    assert Favorite._meta.db_table == "favorites" and not Favorite._meta.managed
    assert Favorite._meta.unique_together == (("userId", "postId"),)
    assert not any(field.is_relation for field in Favorite._meta.fields)


def test_empty_hydration_no_http(client, monkeypatch):
    query = MagicMock()
    query.values_list.return_value = []
    monkeypatch.setattr(selectors, "rows", lambda user: query)
    monkeypatch.setattr(
        clients, "hydrate", lambda *args: pytest.fail("empty favorites must not call Post")
    )
    token = jwt.encode({"id": 42}, settings.JWT_SECRET, algorithm="HS256")
    assert client.get("/my-favorites", HTTP_AUTHORIZATION="Bearer " + token).json() == []


def test_hydration_parallel_order_failure_and_request_id(monkeypatch):
    import httpx

    settings.SERVICE_URLS["POST_SERVICE_URL"] = "http://post.test"
    requests = []

    def respond(request):
        requests.append(request)
        identifier = int(request.url.path[1:])
        if identifier == 2:
            return httpx.Response(404)
        if identifier == 3:
            return httpx.Response(200, content=b"not json")
        return httpx.Response(200, json={"id": identifier, "price": 1.25})

    real = httpx.Client
    monkeypatch.setattr(
        clients.httpx,
        "Client",
        lambda **kwargs: real(transport=httpx.MockTransport(respond), **kwargs),
    )
    assert clients.hydrate(range(1, 19), "unit-request") == [
        {"id": i, "price": 1.25} for i in range(1, 19) if i not in {2, 3}
    ]
    assert len(requests) == 18 and all(
        r.headers["X-Request-ID"] == "unit-request" for r in requests
    )
