import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from conftest import (
    A,
    B,
    C,
    compare,
    container,
    docker,
    events,
    headers,
    seed_messages,
    select,
    wait_for,
)


@pytest.mark.parametrize(
    "path", ["/contacts", f"/{B}", "/notifications", "/notifications/read-all", "/"]
)
@pytest.mark.parametrize("kind", ["missing", "invalid", "wrong", "expired"])
def test_protected_routes(live, path, kind):
    client, urls = live
    method = "PUT" if "read-all" in path else "POST" if path == "/" else "GET"
    responses = [
        client.request(method, url + path, headers=headers(kind), json={})
        for url in urls["message"].values()
    ]
    assert responses[0].status_code == responses[1].status_code == 401
    compare(responses[0].json(), responses[1].json())


@pytest.mark.parametrize("contact", [B, C, 99999999, "not-a-number", f"{B}suffix"])
def test_history_both_directions_oldest_first(live, contact):
    seed_messages()
    client, urls = live
    payloads = [
        client.get(url + f"/{contact}", headers=headers()).json()
        for url in urls["message"].values()
    ]
    compare(*payloads)
    if contact == B:
        assert [row["content"] for row in payloads[1]["data"]] == ["first", "reply"]
        assert set(payloads[1]["data"][0]) == {
            "id",
            "senderId",
            "receiverId",
            "content",
            "isRead",
            "createdAt",
            "updatedAt",
        }


@pytest.mark.parametrize("mode", [None, "failure", "invalid"])
def test_contacts_order_enrichment_and_fallback(live, mode):
    seed_messages()
    client, urls = live
    payloads = []
    for runtime in ("node", "python"):
        client.post(
            urls["dependencies"][runtime] + "/__control", json={"USER": mode} if mode else {}
        )
        response = client.get(urls["message"][runtime] + "/contacts", headers=headers())
        assert response.status_code == 200
        payloads.append(response.json())
    compare(*payloads)
    assert [row["id"] for row in payloads[1]["data"]] == [B, C]
    assert payloads[1]["data"][0]["lastMessage"]["content"] == "reply"
    assert payloads[1]["data"][1]["user"] == {"id": C, "username": f"User {C}"}
    assert all(e["requestId"] == "phase6-parity" for e in events(live, "python"))


@pytest.mark.parametrize(
    "body",
    [
        {"receiverId": B, "content": "synthetic phase6 tiếng Việt 💬"},
        {"receiverId": str(B), "content": "string identifier"},
        {"receiverId": B, "content": ""},
        {"receiverId": B, "content": 123},
        {"receiverId": 99999999, "content": "offline unknown"},
    ],
)
def test_send_payload_persistence_and_dependencies(live, body):
    client, urls = live
    payloads = []
    for runtime in ("node", "python"):
        response = client.post(
            urls["message"][runtime] + "/", json={**body, "senderId": C}, headers=headers()
        )
        assert response.status_code == 200
        payloads.append(response.json())
        persisted = json.loads(
            select(
                "message",
                "SET NAMES utf8mb4; SELECT JSON_OBJECT('senderId',senderId,'receiverId',receiverId,"
                "'content',content,'isRead',isRead) "
                f"FROM phase6_message_{runtime}.messages WHERE id={response.json()['data']['id']}",
            )
        )
        assert persisted == {
            "senderId": A,
            "receiverId": int(body["receiverId"]),
            "content": str(body["content"]),
            "isRead": 0,
        }
        captured = events(live, runtime)
        assert [e["dependency"] for e in captured] == (
            ["AUTH"] if body["receiverId"] == 99999999 else ["AUTH", "NOTIFICATION"]
        )
        if len(captured) == 2:
            assert captured[1]["payload"]["to"] == f"phase6_{B}@example.invalid"
            assert "Bạn có tin nhắn mới" in captured[1]["payload"]["subject"]
    compare(*payloads, generated=True)
    assert all(e["requestId"] == "phase6-parity" for e in events(live, "python"))


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"receiverId": B},
        {"content": "missing receiver"},
        {"receiverId": B, "content": {}},
        {"receiverId": B, "content": []},
    ],
)
def test_send_validation(live, body):
    client, urls = live
    responses = [
        client.post(url + "/", json=body, headers=headers()) for url in urls["message"].values()
    ]
    assert responses[0].status_code == responses[1].status_code == 500
    compare(responses[0].json(), responses[1].json())


@pytest.mark.parametrize(
    "dependency,mode",
    [
        ("AUTH", "failure"),
        ("AUTH", "invalid"),
        ("NOTIFICATION", "failure"),
        ("NOTIFICATION", "invalid"),
        ("AUTH", "network"),
        ("NOTIFICATION", "network"),
    ],
)
def test_dependency_failure_keeps_message_and_emits(live, sockets, dependency, mode):
    client, urls = live
    for runtime in ("node", "python"):
        sockets.call(
            "connect",
            client=runtime,
            url=urls["message"][runtime],
            userId=B,
            transports=["websocket"],
        )
        client.post(urls["dependencies"][runtime] + "/__control", json={dependency: mode})
        response = client.post(
            urls["message"][runtime] + "/",
            headers=headers(),
            json={"receiverId": B, "content": "synthetic failure"},
        )
        assert response.status_code == 200
        event = sockets.call(
            "wait", client=runtime, event="receive_message", id=response.json()["data"]["id"]
        )
        assert event["payload"] == response.json()["data"]
        assert (
            select("message", f"SELECT COUNT(*) FROM phase6_message_{runtime}.messages").strip()
            == "1"
        )


@pytest.mark.parametrize(
    "body",
    [
        {"receiverId": B, "title": "title", "message": "body"},
        {"receiverId": str(B), "title": "title", "message": "body", "link": "/posts/42"},
        {"receiverId": B, "title": "", "message": "", "link": None},
    ],
)
def test_public_notification_create(live, body):
    client, urls = live
    responses = [client.post(url + "/notifications", json=body) for url in urls["message"].values()]
    assert all(r.status_code == 200 for r in responses)
    compare(responses[0].json(), responses[1].json(), generated=True)
    assert responses[1].json()["success"] is True


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"receiverId": B},
        {"receiverId": B, "title": "x"},
        {"receiverId": B, "title": {}, "message": "x"},
    ],
)
def test_notification_validation(live, body):
    client, urls = live
    responses = [client.post(url + "/notifications", json=body) for url in urls["message"].values()]
    assert responses[0].status_code == responses[1].status_code == 500
    compare(responses[0].json(), responses[1].json())


def test_notification_route_shadow_fix_and_dormant_node_handler(live):
    client, urls = live
    for runtime in ("node", "python"):
        values = ",".join(
            f"({i},{A},'n{i}','synthetic',0,NULL,"
            f"DATE_ADD('2026-01-01',INTERVAL {i} SECOND),"
            f"DATE_ADD('2026-01-01',INTERVAL {i} SECOND))"
            for i in range(1, 56)
        )
        select(
            "message",
            f"INSERT INTO phase6_message_{runtime}.notifications "
            "(id,userId,title,message,isRead,link,createdAt,updatedAt) VALUES " + values,
        )
        select(
            "message",
            f"INSERT INTO phase6_message_{runtime}.notifications "
            "(userId,title,message,isRead,createdAt,updatedAt) "
            f"VALUES ({B},'other','other',0,NOW(),NOW())",
        )
    old = client.get(urls["message"]["node"] + "/notifications", headers=headers()).json()
    assert old == {"data": []}, "Document the live Node shadowed history response"
    fixed = client.get(urls["message"]["python"] + "/notifications", headers=headers()).json()
    assert len(fixed["data"]) == 50 and [r["id"] for r in fixed["data"]] == list(range(55, 5, -1))
    # Invoke the legacy dormant selector read-only, proving intended handler parity.
    script = (
        "const q=require('/app/src/queries/notificationQueries');"
        "(async()=>{const r=await q.getNotificationsHandler("
        + str(A)
        + ");process.stdout.write('RESULT'+JSON.stringify(r));"
        "process.exit(0)})().catch(()=>process.exit(1));"
    )
    result = docker("exec", container("message-phase6-node"), "node", "-e", script)
    intended = json.loads(result.split("RESULT")[-1])
    compare(intended, fixed["data"])
    for runtime in ("node", "python"):
        response = client.put(
            urls["message"][runtime] + "/notifications/read-all", headers=headers()
        )
        assert response.json() == {"success": True}
        assert (
            select(
                "message",
                f"SELECT COUNT(*) FROM phase6_message_{runtime}.notifications "
                f"WHERE userId={A} AND isRead=0",
            ).strip()
            == "0"
        )
        assert (
            select(
                "message",
                f"SELECT COUNT(*) FROM phase6_message_{runtime}.notifications "
                f"WHERE userId={B} AND isRead=0",
            ).strip()
            == "1"
        )


@pytest.mark.parametrize("runtime", ["node", "python"])
def test_persist_then_await_email_then_emit(live, sockets, runtime):
    client, urls = live
    sockets.call(
        "connect", client="b", url=urls["message"][runtime], userId=B, transports=["websocket"]
    )
    control = urls["dependencies"][runtime]
    client.post(control + "/__control", json={"NOTIFICATION": "delay"})
    auth = headers()
    with ThreadPoolExecutor(max_workers=1) as pool:
        operation = pool.submit(
            client.post,
            urls["message"][runtime] + "/",
            headers=auth,
            json={"receiverId": B, "content": "synthetic awaited email"},
        )
        wait_for(lambda: any(e["dependency"] == "NOTIFICATION" for e in events(live, runtime)))
        assert (
            select("message", f"SELECT COUNT(*) FROM phase6_message_{runtime}.messages").strip()
            == "1"
        )
        assert not operation.done(), "HTTP send must still await the email HTTP transport"
        assert sockets.call("events", client="b")["events"] == []
        response = operation.result(timeout=15)
    assert response.status_code == 200
    assert (
        sockets.call("wait", client="b", event="receive_message", id=response.json()["data"]["id"])[
            "payload"
        ]
        == response.json()["data"]
    )
