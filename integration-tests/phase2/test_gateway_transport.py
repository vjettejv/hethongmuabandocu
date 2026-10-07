import asyncio
import hashlib
import json

import pytest
from conftest import published_url
from websockets.asyncio.client import connect


def test_real_wire_multipart_streaming_and_forwarded_metadata(live):
    client, _ = live
    url = published_url("gateway-probe", 3000)
    beginning = (
        b'--phase2-boundary\r\nContent-Disposition: form-data; name="images"; '
        b'filename="synthetic.bin"\r\nContent-Type: application/octet-stream\r\n\r\n'
    )
    chunks = [beginning] + [b"\x00\xff" * 32768] * 16 + [b"\r\n--phase2-boundary--\r\n"]
    expected = hashlib.sha256()
    for chunk in chunks:
        expected.update(chunk)
    response = client.post(
        url + "/posts?categoryId=1&query=a%2Bb",
        content=iter(chunks),
        headers={
            "Content-Type": "multipart/form-data; boundary=phase2-boundary",
            "Authorization": "Bearer synthetic-wire-fixture",
            "X-Request-ID": "multipart-phase2",
        },
    )
    assert response.status_code == 201
    result = response.json()
    assert result["method"] == "POST"
    assert result["path"] == "/?categoryId=1&query=a%2Bb"
    assert result["size"] == sum(map(len, chunks))
    assert result["sha256"] == expected.hexdigest()
    assert result["chunks"] > 1
    assert result["contentType"] == "multipart/form-data; boundary=phase2-boundary"
    assert result["requestId"] == response.headers["x-request-id"] == "multipart-phase2"
    assert result["authorizationPresent"]


def test_real_wire_binary_upload_response(live):
    client, _ = live
    response = client.get(published_url("gateway-probe", 3000) + "/uploads/fixture.bin")
    assert response.status_code == 200
    assert response.content == bytes([0, 255, 1, 2, 3, 13, 10])
    assert response.headers["content-type"] == "application/octet-stream"
    assert response.headers["content-length"] == "7"
    assert response.headers["cache-control"] == "public, max-age=60"
    assert response.headers["etag"] == '"fixture"'
    assert response.headers.get_list("set-cookie") == ["a=1", "b=2"]


@pytest.mark.parametrize(
    "base,origin",
    [
        ("http://127.0.0.1:3000", "http://localhost:5173"),
        ("http://127.0.0.1:80", "http://localhost:80"),
        ("http://127.0.0.1:80", "http://localhost"),
        ("http://127.0.0.1:80", "http://127.0.0.1"),
    ],
)
def test_node_socketio_polling_upgrade_and_namespace_through_gateway(live, base, origin):
    client, _ = live
    polling = client.get(base + "/socket.io/?EIO=4&transport=polling", headers={"Origin": origin})
    assert polling.status_code == 200 and polling.text.startswith("0")
    handshake = json.loads(polling.text[1:])
    assert "websocket" in handshake["upgrades"]

    async def upgrade():
        url = (
            base.replace("http://", "ws://")
            + "/socket.io/?EIO=4&transport=websocket&sid="
            + handshake["sid"]
        )
        async with connect(url, origin=origin, proxy=None, open_timeout=8) as websocket:
            await websocket.send("2probe")
            assert await asyncio.wait_for(websocket.recv(), 8) == "3probe"
            await websocket.send("5")
            await websocket.send("40")
            connected = await asyncio.wait_for(websocket.recv(), 8)
            assert connected.startswith("40") and "sid" in json.loads(connected[2:])
            await websocket.send('42["join_user_room","phase2-synthetic-room"]')
            await websocket.send("41")

    asyncio.run(upgrade())


def test_frontend_nginx_routes_and_cors(live):
    client, _ = live
    assert client.get("http://127.0.0.1:80/").status_code == 200
    for path in ["/posts", "/categories"]:
        direct = client.get("http://127.0.0.1:3000" + path)
        frontend = client.get("http://127.0.0.1:80" + path)
        assert direct.status_code == frontend.status_code == 200
        assert direct.json() == frontend.json()
    preflight = client.options(
        "http://127.0.0.1:3000/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization, Content-Type, X-Request-ID",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "POST" in preflight.headers["access-control-allow-methods"]
