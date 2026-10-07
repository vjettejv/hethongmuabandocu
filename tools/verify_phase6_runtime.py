"""Guarded all-Python canonical E2E with real Socket.IO 4.x events.

Run only while Search uses the owned schema in phase6.e2e. Synthetic rows
are journalled and removed by exact account/post guards; uploads are never written.
"""

import json
import secrets
import subprocess
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import httpx
from phase6_socket import SocketClient
from verify_phase4_runtime import literal
from verify_runtime import command, container_name, select

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / ".artifacts/phase6"


def environment(service):
    row = json.loads(command(["docker", "inspect", service]))[0]
    return dict(item.split("=", 1) for item in row["Config"]["Env"] if "=" in item)


def wait_for(check):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        result = check()
        if result:
            return result
        time.sleep(0.1)
    raise AssertionError("Canonical side effect missing")


def private_logs(service, since):
    result = subprocess.run(
        ["docker", "logs", "--since", since, container_name(service)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=True,
    )
    return result.stdout + result.stderr


def main():
    assert environment("search-service")["DB_NAME"] == "phase6_search_e2e"
    assert "phase6_search_e2e" in json.loads((ARTIFACTS / "test-databases.json").read_text())
    assert select("search", "SELECT COUNT(*) FROM phase6_search_e2e.searchindices").strip() == "0"
    assert environment("post-service")["MESSAGE_SERVICE_URL"] == "http://message-service:3005"
    assert environment("notification-service").get("MOCK_EMAIL") == "true"
    for service, image in [
        ("message-service", "kientrucpm-message-python-phase6"),
        ("notification-service", "kientrucpm-notification-python-phase6"),
    ]:
        assert (
            command(["docker", "inspect", service, "--format", "{{.Config.Image}}"]).strip()
            == image
        )
    marker = "phase6_test_" + uuid.uuid4().hex
    started = datetime.now(UTC).isoformat()
    accounts, posts, safe_ids, private = [], [], [], []
    checks = []

    def passed(label):
        checks.append(label)
        print("PASS:", label, flush=True)

    def journal():
        (ARTIFACTS / "runtime-owned.json").write_text(
            json.dumps(
                {
                    "marker": marker,
                    "accountIds": [row["id"] for row in accounts],
                    "postIds": posts,
                    "safeIds": safe_ids,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def count(kind, table, condition):
        return int(
            select(kind, f"SELECT COUNT(*) FROM {kind}_db.{table} WHERE {condition}").strip()
        )

    with httpx.Client(base_url="http://127.0.0.1:3000", timeout=40, trust_env=False) as client:
        try:
            for suffix in ("a", "b", "c"):
                name, email, password = (
                    marker + "_" + suffix,
                    marker + "_" + suffix + "@example.invalid",
                    secrets.token_urlsafe(32),
                )
                request_id = marker + "_register_" + suffix
                response = client.post(
                    "/auth/register",
                    json={"username": name, "email": email, "password": password},
                    headers={"X-Request-ID": request_id},
                )
                assert response.status_code == 201
                identifier = response.json()["userId"]
                account = {"id": identifier, "name": name, "email": email}
                accounts.append(account)
                journal()
                guard = f"id={identifier} AND username={literal(name)} AND email={literal(email)}"
                assert count("user", "userprofiles", f"authId={identifier}") == 0
                assert (
                    count(
                        "message", "messages", f"senderId={identifier} OR receiverId={identifier}"
                    )
                    == 0
                )
                assert count("message", "notifications", f"userId={identifier}") == 0
                assert count("post", "posts", f"userId={identifier}") == 0
                safe_ids.append(identifier)
                journal()
                otp = select("auth", f"SELECT otp FROM auth_db.users WHERE {guard}").strip()
                assert (
                    client.post(
                        "/auth/verify-otp",
                        json={"email": email, "otp": otp},
                        headers={"X-Request-ID": marker + "_otp_" + suffix},
                    ).status_code
                    == 200
                )
                login = client.post("/auth/login", json={"email": email, "password": password})
                assert login.status_code == 200
                token = login.json()["token"]
                account["headers"] = {
                    "Authorization": "Bearer " + token,
                    "X-Request-ID": marker + "_" + suffix,
                }
                private.extend([password, token, otp])
                assert (
                    client.get("/users/me", headers=account["headers"]).json()["authId"]
                    == identifier
                )
                assert (
                    client.put(
                        "/users/me", headers=account["headers"], json={"fullName": name}
                    ).status_code
                    == 200
                )
            passed(
                "three real Auth register/OTP/login JWTs -> real User profiles -> Python mock email"
            )
            a, b, c = accounts
            with SocketClient() as sockets:
                # Nginx :80 and direct Gateway :3000 both reach canonical Python Message.
                for name, url, user, transport, upgrade in [
                    ("b", "http://127.0.0.1", b["id"], ["polling", "websocket"], True),
                    ("b2", "http://127.0.0.1:3000", str(b["id"]), ["websocket"], False),
                    ("c", "http://127.0.0.1", c["id"], ["polling"], False),
                    ("a", "http://127.0.0.1:3000", a["id"], ["websocket"], False),
                ]:
                    state = sockets.call(
                        "connect",
                        client=name,
                        url=url,
                        userId=user,
                        transports=transport,
                        upgrade=upgrade,
                    )
                    assert state["connected"]
                    assert state["transport"] == ("websocket" if upgrade else transport[0])
                passed(
                    "unchanged frontend Socket.IO 4 client via Nginx/Gateway: "
                    "polling, WebSocket and upgrade"
                )
                secret_body = marker + " private_message_sentinel"
                private.append(secret_body)
                response = client.post(
                    "/messages",
                    headers=a["headers"],
                    json={"senderId": c["id"], "receiverId": b["id"], "content": secret_body},
                )
                assert response.status_code == 200
                message = response.json()["data"]
                assert message["senderId"] == a["id"] and message["receiverId"] == b["id"]
                for name in ("b", "b2"):
                    assert (
                        sockets.call(
                            "wait", client=name, event="receive_message", id=message["id"]
                        )["payload"]
                        == message
                    )
                assert sockets.call("events", client="c")["events"] == []
                assert sockets.call("events", client="a")["events"] == []
                passed(
                    "Message JWT sender -> persist -> real Auth lookup/awaited Python mock email "
                    "-> two receiver sockets; room isolation"
                )
                response = client.post(
                    "/messages",
                    headers=b["headers"],
                    json={"receiverId": a["id"], "content": marker + " reverse"},
                )
                assert response.status_code == 200
                assert (
                    sockets.call(
                        "wait",
                        client="a",
                        event="receive_message",
                        id=response.json()["data"]["id"],
                    )["payload"]
                    == response.json()["data"]
                )
                history = client.get(f"/messages/{b['id']}", headers=a["headers"]).json()["data"]
                assert {row["id"] for row in history} == {
                    message["id"],
                    response.json()["data"]["id"],
                }
                contacts = client.get("/messages/contacts", headers=a["headers"]).json()["data"]
                assert len(contacts) == 1 and contacts[0]["user"]["fullName"] == b["name"]
                passed("both-direction history and contacts enriched by real canonical User HTTP")
                for name in ("b", "b2"):
                    sockets.call("disconnect", client=name)
                offline = client.post(
                    "/messages",
                    headers=a["headers"],
                    json={"receiverId": b["id"], "content": marker + " offline"},
                )
                assert offline.status_code == 200
                assert any(
                    row["id"] == offline.json()["data"]["id"]
                    for row in client.get(f"/messages/{a['id']}", headers=b["headers"]).json()[
                        "data"
                    ]
                )
                sockets.call("clear")
                sockets.call(
                    "connect",
                    client="b",
                    url="http://127.0.0.1",
                    userId=b["id"],
                    transports=["polling", "websocket"],
                    upgrade=True,
                )
                assert sockets.call("events", client="b")["events"] == []
                after = client.post(
                    "/messages",
                    headers=a["headers"],
                    json={"receiverId": b["id"], "content": marker + " reconnect"},
                )
                assert (
                    sockets.call(
                        "wait", client="b", event="receive_message", id=after.json()["data"]["id"]
                    )["payload"]
                    == after.json()["data"]
                )
                passed(
                    "offline messages remain in MySQL; reconnect and explicit rejoin "
                    "receive subsequent events"
                )
                sockets.call("clear")
                notification = client.post(
                    "/messages/notifications",
                    json={
                        "receiverId": b["id"],
                        "title": marker,
                        "message": marker + " notification",
                        "link": "/posts/phase6",
                    },
                    headers={"X-Request-ID": marker + "_notification"},
                )
                assert notification.status_code == 200 and notification.json()["success"]
                assert (
                    sockets.call(
                        "wait",
                        client="b",
                        event="receive_notification",
                        id=notification.json()["data"]["id"],
                    )["payload"]
                    == notification.json()["data"]
                )
                assert sockets.call("events", client="c")["events"] == []
                assert client.put(
                    "/messages/notifications/read-all", headers=b["headers"]
                ).json() == {"success": True}
                assert all(
                    row["isRead"]
                    for row in client.get("/messages/notifications", headers=b["headers"]).json()[
                        "data"
                    ]
                )
                passed(
                    "public in-app create -> actual receive_notification; "
                    "reachable list and authenticated read-all"
                )
                category = client.get("/categories").json()[0]
                created = client.post(
                    "/posts",
                    headers=a["headers"],
                    json={
                        "categoryId": category["id"],
                        "title": marker,
                        "price": 12.34,
                        "description": "",
                    },
                )
                assert created.status_code == 201
                post_id = created.json()["post"]["id"]
                posts.append(post_id)
                journal()
                wait_for(
                    lambda: (
                        select(
                            "search",
                            "SELECT COUNT(*) FROM phase6_search_e2e.searchindices "
                            f"WHERE postId={post_id} AND title={literal(marker)}",
                        ).strip()
                        == "1"
                    )
                )
                seen = set()
                for status in ("approved", "rejected", "approved"):
                    sockets.call("clear")
                    response = client.put(
                        f"/admin/posts/{post_id}", headers=a["headers"], json={"status": status}
                    )
                    assert response.status_code == 200
                    rows = wait_for(
                        lambda: [
                            row
                            for row in client.get(
                                "/messages/notifications", headers=a["headers"]
                            ).json()["data"]
                            if row["id"] not in seen
                        ]
                    )
                    latest = rows[0]
                    seen.add(latest["id"])
                    payload = sockets.call(
                        "wait", client="a", event="receive_notification", id=latest["id"]
                    )["payload"]
                    assert payload["userId"] == a["id"] and payload["title"] == latest["title"]
                    assert sockets.call("events", client="c")["events"] == []
                    wait_for(
                        lambda status=status: (
                            select(
                                "search",
                                "SELECT status FROM phase6_search_e2e.searchindices "
                                f"WHERE postId={post_id}",
                            ).strip()
                            == status
                        )
                    )
                assert count("message", "notifications", f"userId={a['id']}") == 3
                sockets.call("clear")
                assert (
                    client.put(
                        f"/admin/posts/{post_id}",
                        headers=a["headers"],
                        json={"status": "approved"},
                    ).status_code
                    == 200
                )
                wait_for(
                    lambda: (
                        select(
                            "search",
                            "SELECT status FROM phase6_search_e2e.searchindices "
                            f"WHERE postId={post_id}",
                        ).strip()
                        == "approved"
                    )
                )
                assert count("message", "notifications", f"userId={a['id']}") == 3
                assert sockets.call("events", client="a")["events"] == []
                assert count("message", "notifications", f"userId={b['id']} AND isRead=0") == 0
                client.put("/messages/notifications/read-all", headers=a["headers"])
                passed(
                    "unchanged canonical Post -> Python Message: approve/reject/repeated "
                    "moderation, three real events and read-all ownership"
                )
                assert client.post("/notifications/email", json={}).json() == {
                    "message": "Email queued (Mock)",
                    "mock": True,
                }
                passed("Gateway /notifications/email -> DB-less Python mock email contract")
            # Read logs privately; publish only verification outcome.
            logs = private_logs("notification-service", started)
            # Docker stdout logging is forwarded by the formatter; no body inspection artifact.
            assert marker + "_register_a" in logs or marker + "_a" in logs
            all_logs = logs + private_logs("message-service", started)
            assert all(value not in all_logs for value in private)
            passed(
                "request IDs propagated; Message/Notification logs contain no synthetic "
                "JWT/OTP/password/private message"
            )
        finally:
            # Account guards and proven empty dependent rows constrain all cleanup.
            # The unchanged Post uses a bounded four-thread HTTP executor. Allow
            # its few synthetic dispatches to settle even after an early failure.
            if posts:
                time.sleep(8)
            for post_id in posts:
                owner = accounts[0]["id"]
                assert count(
                    "post", "posts", f"id={post_id} AND userId={owner} AND title={literal(marker)}"
                ) in (0, 1)
                assert count("post", "images", f"postId={post_id}") == 0
                select(
                    "post",
                    f"DELETE FROM post_db.posts WHERE id={post_id} AND userId={owner} "
                    f"AND title={literal(marker)}",
                )
                select(
                    "search",
                    f"DELETE FROM phase6_search_e2e.searchindices WHERE postId={post_id} "
                    f"AND title={literal(marker)}",
                )
            if safe_ids:
                ids = ",".join(map(str, safe_ids))
                select(
                    "message",
                    f"DELETE FROM message_db.messages WHERE (senderId IN ({ids}) "
                    f"OR receiverId IN ({ids})) AND content LIKE {literal(marker + '%')}",
                )
                select("message", f"DELETE FROM message_db.notifications WHERE userId IN ({ids})")
                assert (
                    count("message", "messages", f"senderId IN ({ids}) OR receiverId IN ({ids})")
                    == 0
                )
                assert count("message", "notifications", f"userId IN ({ids})") == 0
                select(
                    "user",
                    f"DELETE FROM user_db.userprofiles WHERE authId IN ({ids}) "
                    f"AND fullName LIKE {literal(marker + '%')}",
                )
            for row in accounts:
                guard = (
                    f"id={row['id']} AND username={literal(row['name'])} "
                    f"AND email={literal(row['email'])}"
                )
                select("auth", f"DELETE FROM auth_db.users WHERE {guard}")
                assert count("auth", "users", guard) == 0
            assert (
                select("search", "SELECT COUNT(*) FROM phase6_search_e2e.searchindices").strip()
                == "0"
            )
            passed(
                "guarded synthetic accounts/profiles/messages/notifications/posts/"
                "search projections removed; no upload created"
            )
            (ARTIFACTS / "canonical-checks.json").write_text(
                json.dumps(checks, indent=2) + "\n", encoding="utf-8"
            )


if __name__ == "__main__":
    main()
