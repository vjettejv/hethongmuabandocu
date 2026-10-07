import gzip
import json

import httpx
import pytest
from app.main import create_app
from app.settings import Settings
from fastapi.testclient import TestClient


@pytest.fixture
def upstream():
    calls = []

    async def handler(request):
        calls.append(request)
        content = await request.aread()
        response = json.dumps(
            {
                "method": request.method,
                "path": request.url.raw_path.decode(),
                "host": request.url.host,
                "body": content.decode("latin-1"),
                "headers": dict(request.headers),
            }
        ).encode()
        return httpx.Response(
            207, headers={"content-type": "application/json"}, stream=httpx.ByteStream(response)
        )

    urls = {
        f"{service}_service_url": f"http://{service}.invalid"
        for service in (
            "auth",
            "user",
            "post",
            "category",
            "message",
            "notification",
            "review",
            "search",
            "favorite",
        )
    }
    with TestClient(
        create_app(
            Settings(**urls, cors_allowed_origins="http://localhost:5173"),
            configure_logging=False,
            transport=httpx.MockTransport(handler),
        )
    ) as client:
        yield client, calls


@pytest.mark.parametrize(
    "prefix,host,rewrite",
    [
        ("/auth", "auth", "/item"),
        ("/users", "user", "/item"),
        ("/posts", "post", "/item"),
        ("/categories", "category", "/item"),
        ("/messages", "message", "/item"),
        ("/notifications", "notification", "/item"),
        ("/reviews", "review", "/item"),
        ("/search", "search", "/item"),
        ("/favorites", "favorite", "/item"),
        ("/admin/posts", "post", "/admin/posts/item"),
        ("/admin/categories", "category", "/admin/categories/item"),
        ("/uploads", "post", "/uploads/item"),
        ("/socket.io", "message", "/socket.io/item"),
    ],
)
@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
def test_routes_all_methods_and_queries(upstream, prefix, host, rewrite, method):
    client, _ = upstream
    response = client.request(method, prefix + "/item?categoryId=2&query=a%2Bb&query=c")
    assert response.status_code == 207
    assert response.json()["host"] == f"{host}.invalid"
    assert response.json()["method"] == method
    assert response.json()["path"] == rewrite + "?categoryId=2&query=a%2Bb&query=c"


@pytest.mark.parametrize(
    "path,expected",
    [
        ("/posts/admin/posts/7", "/admin/posts/7"),
        ("/categories/admin/categories", "/admin/categories"),
        ("/messages/notifications", "/notifications"),
        ("/notifications/email", "/email"),
        ("/auth", "/"),
        ("/posts/", "/"),
        ("/uploads/a%20b.png", "/uploads/a%20b.png"),
    ],
)
def test_aliases_and_raw_paths(upstream, path, expected):
    client, _ = upstream
    assert client.get(path).json()["path"] == expected


def test_json_headers_request_ids_and_forwarded_metadata(upstream):
    client, _ = upstream
    response = client.post(
        "/auth/login",
        json={"username": "synthetic", "password": "test"},
        headers={
            "Authorization": "Bearer synthetic",
            "X-Request-ID": "proxy-test",
            "X-Forwarded-For": "192.0.2.1",
            "Accept": "application/json",
        },
    )
    result = response.json()
    assert json.loads(result["body"]) == {"username": "synthetic", "password": "test"}
    assert result["headers"]["authorization"] == "Bearer synthetic"
    assert result["headers"]["x-request-id"] == response.headers["x-request-id"] == "proxy-test"
    assert result["headers"]["x-forwarded-for"].endswith(", testclient")
    assert result["headers"]["x-forwarded-proto"] == "http"
    assert result["headers"]["host"] == "auth.invalid"


def test_multipart_boundary_and_binary_body(upstream):
    client, _ = upstream
    body = (
        b"--safe-boundary\r\nContent-Disposition: form-data; "
        b'name="images"; filename="x.bin"\r\n\r\n'
        b"\x00\xff\r\n--safe-boundary--\r\n"
    )
    response = client.post(
        "/posts",
        content=body,
        headers={"Content-Type": "multipart/form-data; boundary=safe-boundary"},
    )
    assert response.json()["body"].encode("latin-1") == body
    assert response.json()["headers"]["content-type"].endswith("boundary=safe-boundary")


def test_binary_compressed_duplicate_headers_and_redirect_are_preserved():
    binary = gzip.compress(b"\x00\xffsynthetic image")

    def handler(request):
        return httpx.Response(
            302,
            headers=[
                ("content-type", "application/octet-stream"),
                ("content-encoding", "gzip"),
                ("content-length", str(len(binary))),
                ("cache-control", "public, max-age=60"),
                ("location", "/uploads/other"),
                ("set-cookie", "a=1"),
                ("set-cookie", "b=2"),
                ("connection", "x-hop"),
                ("x-hop", "must-drop"),
            ],
            stream=httpx.ByteStream(binary),
        )

    with TestClient(
        create_app(
            Settings(post_service_url="http://post.invalid"),
            configure_logging=False,
            transport=httpx.MockTransport(handler),
        )
    ) as client:
        response = client.get("/uploads/fixture", follow_redirects=False)
        assert response.status_code == 302
        assert response.content == b"\x00\xffsynthetic image"
        assert response.headers["content-length"] == str(len(binary))
        assert response.headers.get_list("set-cookie") == ["a=1", "b=2"]
        assert response.headers["cache-control"] == "public, max-age=60"
        assert response.headers["location"] == "/uploads/other"
        assert "x-hop" not in response.headers


@pytest.mark.parametrize(
    "failure,status,error",
    [
        (httpx.ConnectError, 502, "Service Unavailable"),
        (httpx.ReadTimeout, 504, "Gateway Timeout"),
    ],
)
def test_upstream_errors_are_controlled(failure, status, error):
    def handler(request):
        raise failure("secret connection information", request=request)

    with TestClient(
        create_app(
            Settings(auth_service_url="http://auth.invalid"),
            configure_logging=False,
            transport=httpx.MockTransport(handler),
        )
    ) as client:
        response = client.post("/auth/login")
        assert response.status_code == status
        assert response.json() == {"error": error}
        assert "secret" not in response.text


def test_head_and_cors_preflight(upstream):
    client, calls = upstream
    assert client.head("/posts").status_code == 207
    before = len(calls)
    response = client.options(
        "/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization, Content-Type, X-Request-ID",
        },
    )
    assert response.status_code == 200 and len(calls) == before
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "POST" in response.headers["access-control-allow-methods"]


def test_prefix_boundary_and_no_global_jwt_check(upstream):
    client, _ = upstream
    assert client.get("/posts-other").status_code == 404
    assert client.get("/api/posts").status_code == 404
    assert client.get("/users/me", headers={"Authorization": "Bearer invalid"}).status_code == 207
    for path in ["/auth/health", "/auth/ready", "/auth/schema/", "/auth/docs/"]:
        assert client.get(path).status_code == 404
