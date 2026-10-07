import pytest
from conftest import A, B, C, headers, select, wait_for


@pytest.mark.parametrize("runtime", ["node", "python"])
@pytest.mark.parametrize(
    "transports,upgrade",
    [(["websocket"], False), (["polling"], False), (["polling", "websocket"], True)],
)
def test_actual_events_multisocket_room_isolation(live, sockets, runtime, transports, upgrade):
    client, urls = live
    for name, user in [("b", B), ("b2", str(B)), ("c", C), ("sender", A)]:
        connected = sockets.call(
            "connect",
            client=name,
            url=urls["message"][runtime],
            userId=user,
            transports=transports,
            upgrade=upgrade,
        )
        assert connected["connected"]
        if upgrade or transports == ["websocket"]:
            assert connected["transport"] == "websocket"
    sockets.call("clear")
    for event, path, body in [
        ("receive_message", "/", {"receiverId": B, "content": "synthetic realtime"}),
        (
            "receive_notification",
            "/notifications",
            {
                "receiverId": B,
                "title": "synthetic title",
                "message": "synthetic body",
                "link": "/posts/1",
            },
        ),
    ]:
        response = client.post(urls["message"][runtime] + path, json=body, headers=headers())
        assert response.status_code == 200
        payload = response.json()["data"]
        for name in ("b", "b2"):
            assert (
                sockets.call("wait", client=name, event=event, id=payload["id"])["payload"]
                == payload
            )
        assert sockets.call("events", client="c")["events"] == []
        assert sockets.call("events", client="sender")["events"] == []


@pytest.mark.parametrize("runtime", ["node", "python"])
def test_offline_persistence_reconnect_rejoin(live, sockets, runtime):
    client, urls = live
    url = urls["message"][runtime]
    sockets.call("connect", client="b", url=url, userId=B, transports=["websocket"])
    sockets.call("disconnect", client="b")
    response = client.post(
        url + "/", headers=headers(), json={"receiverId": B, "content": "synthetic offline"}
    )
    assert response.status_code == 200
    history = client.get(url + f"/{A}", headers=headers(user=B)).json()["data"]
    assert history[0]["content"] == "synthetic offline"
    sockets.call("connect", client="b", url=url, userId=B, transports=["websocket"])
    assert sockets.call("events", client="b")["events"] == []
    response = client.post(
        url + "/", headers=headers(), json={"receiverId": B, "content": "synthetic after rejoin"}
    )
    assert (
        sockets.call("wait", client="b", event="receive_message", id=response.json()["data"]["id"])[
            "payload"
        ]
        == response.json()["data"]
    )


@pytest.mark.parametrize("transport", [["websocket"], ["polling"], ["polling", "websocket"]])
def test_python_gateway_socket_and_rest(live, sockets, transport):
    client, urls = live
    result = sockets.call(
        "connect",
        client="b",
        url=urls["gateway"],
        userId=B,
        transports=transport,
        upgrade=len(transport) == 2,
    )
    assert result["connected"]
    response = client.post(
        urls["gateway"] + "/messages",
        headers=headers(),
        json={"receiverId": B, "content": "synthetic gateway"},
    )
    assert response.status_code == 200
    assert (
        sockets.call("wait", client="b", event="receive_message", id=response.json()["data"]["id"])[
            "payload"
        ]
        == response.json()["data"]
    )
    assert client.post(urls["gateway"] + "/notifications/email", json={}).json()["mock"] is True
    assert (
        client.get(urls["gateway"] + f"/messages/{B}", headers=headers()).json()["data"][0][
            "content"
        ]
        == "synthetic gateway"
    )


@pytest.mark.parametrize("status", ["approved", "rejected"])
def test_post_python_moderation_to_message_event(live, sockets, status):
    client, urls = live
    sockets.call("connect", client="a", url=urls["gateway"], userId=A, transports=["websocket"])
    created = client.post(
        urls["gateway"] + "/posts",
        headers=headers(),
        json={"categoryId": 1, "title": "phase6 synthetic post", "price": 1},
    )
    assert created.status_code == 201
    identifier = created.json()["post"]["id"]
    seen = set()
    for current_status in (status, "rejected" if status == "approved" else "approved"):
        sockets.call("clear")
        response = client.put(
            urls["gateway"] + f"/admin/posts/{identifier}",
            headers=headers(),
            json={"status": current_status},
        )
        assert response.status_code == 200
        rows = wait_for(
            lambda: [
                row
                for row in client.get(
                    urls["gateway"] + "/messages/notifications", headers=headers()
                ).json()["data"]
                if row["id"] not in seen
            ]
        )
        latest = rows[0]
        seen.add(latest["id"])
        assert (
            sockets.call("wait", client="a", event="receive_notification", id=latest["id"])[
                "payload"
            ]["userId"]
            == A
        )
    assert (
        select(
            "message", f"SELECT COUNT(*) FROM phase6_message_python.notifications WHERE userId={A}"
        ).strip()
        == "2"
    )
    sockets.call("clear")
    assert (
        client.put(
            urls["gateway"] + f"/admin/posts/{identifier}",
            headers=headers(),
            json={"status": current_status},
        ).status_code
        == 200
    )
    assert (
        select(
            "message", f"SELECT COUNT(*) FROM phase6_message_python.notifications WHERE userId={A}"
        ).strip()
        == "2"
    )
    assert sockets.call("events", client="a")["events"] == []
    assert client.put(
        urls["gateway"] + "/messages/notifications/read-all", headers=headers()
    ).json() == {"success": True}
