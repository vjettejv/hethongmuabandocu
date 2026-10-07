"""Python-only canonical business flows and immutable contract route coverage."""

import base64
import hashlib
import json
import os
import re
import secrets
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import httpx
import jwt
import pytest
from conftest import ROOT
from integration_helpers import environment, literal, private_logs, wait_for
from socket_client import SocketClient
from upload_inventory import inventory
from verify_runtime import SERVICES, command, select

ARTIFACTS = Path(os.environ.get("CANONICAL_TEST_ARTIFACTS", ROOT / ".artifacts/phase7"))
BASE_URL = os.environ.get("CANONICAL_TEST_BASE_URL", "http://127.0.0.1")
ENDPOINTS = json.loads((ROOT / "contracts/endpoints.json").read_text())["endpoints"]
BODY = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aX1kAAAAASUVORK5CYII="
)


def camel(value):
    if isinstance(value, dict):
        assert all("_" not in key for key in value), "Unexpected external snake_case"
        for item in value.values():
            camel(item)
    elif isinstance(value, list):
        for item in value:
            camel(item)


def scalar(kind, query):
    return select(kind, query).strip()


def test_full_business_lifecycle():
    assert environment("search-service")["DB_NAME"] == "phase7_search_e2e"
    assert environment("notification-service")["MOCK_EMAIL"] == "true"
    assert scalar("search", "SELECT COUNT(*) FROM phase7_search_e2e.searchindices") == "0"
    marker = "phase7_test_" + uuid.uuid4().hex
    accounts, posts, reviews, safe, checks, private, timings = [], [], [], [], [], [], {}
    started = datetime.now(UTC).isoformat()
    baseline_uploads = inventory()

    def passed(label):
        checks.append(label)
        print("PASS:", label, flush=True)

    def journal():
        (ARTIFACTS / "runtime-owned.json").write_text(
            json.dumps(
                {
                    "marker": marker,
                    "accounts": [a["id"] for a in accounts],
                    "safeIds": safe,
                    "posts": posts,
                    "reviews": reviews,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def count(kind, table, guard):
        return int(scalar(kind, f"SELECT COUNT(*) FROM {kind}_db.{table} WHERE {guard}"))

    with httpx.Client(
        base_url=BASE_URL,
        timeout=40,
        trust_env=False,
        limits=httpx.Limits(max_keepalive_connections=0),
    ) as client:
        try:
            for suffix in ("a", "b", "c"):
                name = marker + "_" + suffix
                email, password = name + "@example.invalid", secrets.token_urlsafe(32)
                response = client.post(
                    "/auth/register",
                    json={"username": name, "email": email, "password": password},
                    headers={"X-Request-ID": name},
                )
                assert response.status_code == 201
                identifier = response.json()["userId"]
                account = {"id": identifier, "name": name, "email": email}
                accounts.append(account)
                journal()
                for kind, table, guard in (
                    ("user", "userprofiles", f"authId={identifier}"),
                    ("post", "posts", f"userId={identifier}"),
                    ("favorite", "favorites", f"userId={identifier}"),
                    ("review", "reviews", f"reviewerId={identifier} OR revieweeId={identifier}"),
                    ("message", "messages", f"senderId={identifier} OR receiverId={identifier}"),
                    ("message", "notifications", f"userId={identifier}"),
                ):
                    assert count(kind, table, guard) == 0, "Existing dependent ID collision"
                safe.append(identifier)
                journal()
                guard = f"id={identifier} AND username={literal(name)} AND email={literal(email)}"
                otp = scalar("auth", f"SELECT otp FROM auth_db.users WHERE {guard}")
                assert otp and len(otp) == 6
                assert (
                    client.post("/auth/verify-otp", json={"email": email, "otp": otp}).status_code
                    == 200
                )
                assert scalar("auth", f"SELECT isVerified FROM auth_db.users WHERE {guard}") == "1"
                tick = time.monotonic()
                login = client.post("/auth/login", json={"email": email, "password": password})
                timings["login"] = round((time.monotonic() - tick) * 1000, 2)
                assert login.status_code == 200
                token = login.json()["token"]
                assert jwt.get_unverified_header(token)["alg"] == "HS256"
                claims = jwt.decode(
                    token, environment("auth-service")["JWT_SECRET"], algorithms=["HS256"]
                )
                assert claims["id"] == identifier and claims["roleId"] == 1
                assert claims["exp"] - claims["iat"] == 86400
                account["headers"] = {"Authorization": "Bearer " + token, "X-Request-ID": name}
                private.extend([password, token, otp])
                profile = client.get("/users/me", headers=account["headers"]).json()
                assert profile["authId"] == identifier and profile["id"] != identifier
                assert (
                    client.put(
                        "/users/me", headers=account["headers"], json={"fullName": name}
                    ).status_code
                    == 200
                )
                assert client.get(f"/users/{identifier}").json()["fullName"] == name
            passed("A-D: register -> OTP -> real HS256 login -> Auth/Profile IDs and update")
            a, b, c = accounts
            categories = client.get("/categories")
            assert categories.status_code == 200 and categories.json()
            category = categories.json()[0]
            passed("E: existing category read; no category mutation")
            created = client.post(
                "/posts",
                headers=a["headers"],
                data={
                    "categoryId": str(category["id"]),
                    "title": marker,
                    "description": marker,
                    "price": "12.34",
                    "condition": "used",
                },
                files={"images": (marker + "_post.png", BODY, "image/png")},
            )
            assert created.status_code == 201
            post = created.json()["post"]
            pid = post["id"]
            posts.append(pid)
            journal()
            detail = client.get(f"/posts/{pid}").json()
            camel(detail)
            assert isinstance(detail["price"], (int, float)) and detail["price"] == 12.34
            assert detail["Category"]["id"] == category["id"] and len(detail["Images"]) == 1
            assert detail["createdAt"].endswith("Z") and detail["updatedAt"].endswith("Z")
            url = detail["Images"][0]["imageUrl"]
            assert count("post", "images", f"postId={pid} AND imageUrl={literal(url)}") == 1
            for path in ("/posts", "/posts/my-posts"):
                assert any(
                    row["id"] == pid for row in client.get(path, headers=a["headers"]).json()
                )
            uploaded = client.get(url)
            assert uploaded.status_code == 200 and uploaded.content == BODY
            assert client.head(url).headers["content-length"] == str(len(BODY))
            ranged = client.get(url, headers={"Range": "bytes=1-7"})
            assert ranged.status_code == 206 and ranged.content == BODY[1:8]
            assert (
                client.get(url, headers={"If-None-Match": uploaded.headers["etag"]}).status_code
                == 304
            )
            passed(
                "F-G: multipart Post, images metadata, reads, camelCase/price, "
                "GET/HEAD/range/conditional bytes"
            )
            wait_for(
                lambda: (
                    scalar(
                        "search",
                        f"SELECT COUNT(*) FROM phase7_search_e2e.searchindices "
                        f"WHERE postId={pid} AND title={literal(marker)}",
                    )
                    == "1"
                )
            )
            assert client.get("/search", params={"q": marker}).json() == []
            with SocketClient() as sockets:
                for name, account, transports, upgrade in (
                    ("a", a, ["polling", "websocket"], True),
                    ("b", b, ["polling"], False),
                    ("c", c, ["websocket"], False),
                ):
                    state = sockets.call(
                        "connect",
                        client=name,
                        url=BASE_URL,
                        userId=account["id"],
                        transports=transports,
                        upgrade=upgrade,
                    )
                    assert state["connected"] and state["transport"] == (
                        "websocket" if upgrade else transports[0]
                    )
                passed(
                    "K: real frontend Socket.IO EIO4 via Nginx -> Gateway -> "
                    "Python; polling/WS/upgrade/join"
                )
                assert (
                    client.put(
                        f"/admin/posts/{pid}", headers=a["headers"], json={"status": "approved"}
                    ).status_code
                    == 200
                )
                notice = wait_for(
                    lambda: client.get("/messages/notifications", headers=a["headers"]).json()[
                        "data"
                    ]
                )[0]
                event = sockets.call(
                    "wait", client="a", event="receive_notification", id=notice["id"]
                )["payload"]
                assert event["userId"] == a["id"] and event["title"] == notice["title"]
                found = wait_for(lambda: client.get("/search", params={"q": marker}).json())
                assert len(found) == 1 and found[0]["id"] == pid and found[0]["price"] == "12.34"
                camel(found)
                passed(
                    "H/O: actual moderation -> Search fixed decimal -> Message "
                    "DB and realtime owner notification"
                )
                for alias in ("/admin/posts", "/posts/admin/posts"):
                    assert client.get(alias, headers=a["headers"]).status_code == 200
                # Category admin only declares POST; GET proves dispatch with 405.
                for alias in ("/admin/categories", "/categories/admin/categories"):
                    assert client.get(alias, headers=a["headers"]).status_code == 405
                passed("aliases: admin Post/Category direct and legacy prefixed paths")
                assert (
                    client.post(
                        "/favorites/toggle", headers=b["headers"], json={"postId": pid}
                    ).status_code
                    == 201
                )
                assert client.get(f"/favorites/check/{pid}", headers=b["headers"]).json()[
                    "isFavorited"
                ]
                hydrated = client.get("/favorites/my-favorites", headers=b["headers"]).json()
                assert len(hydrated) == 1 and hydrated[0]["id"] == pid and hydrated[0]["Images"]
                assert (
                    client.post(
                        "/favorites/toggle", headers=b["headers"], json={"postId": pid}
                    ).json()["isFavorited"]
                    is False
                )
                passed("I: Favorite add/check -> real Post hydration -> remove")
                review = client.post(
                    "/reviews",
                    data={
                        "reviewerId": str(b["id"]),
                        "revieweeId": str(a["id"]),
                        "postId": str(pid),
                        "rating": "5",
                        "comment": marker,
                    },
                    files={"image": (marker + "_review.png", BODY, "image/png")},
                )
                assert review.status_code == 201
                row = review.json()
                rid = row["id"]
                reviews.append(rid)
                journal()
                review_url = row["imageUrl"]
                assert count("review", "reviews", f"id={rid} AND comment={literal(marker)}") == 1
                assert client.get(review_url).content == BODY
                assert any(r["id"] == rid for r in client.get(f"/reviews/user/{a['id']}").json())
                assert (
                    client.put(
                        f"/reviews/{rid}", json={"rating": 4, "comment": marker + " updated"}
                    ).status_code
                    == 200
                )
                assert client.delete(f"/reviews/{rid}").status_code == 200
                assert client.get(review_url).status_code == 404
                passed("J: multipart Review DB/shared file -> list/update/delete -> safe unlink")
                message_ids = []
                for sender, receiver, target in ((a, b, "b"), (b, a, "a")):
                    content = marker + " message " + target
                    private.append(content)
                    email_calls_before = private_logs("notification-service", started).count(
                        sender["name"]
                    )
                    result = client.post(
                        "/messages",
                        headers=sender["headers"],
                        json={"receiverId": receiver["id"], "content": content},
                    )
                    assert result.status_code == 200
                    assert (
                        private_logs("notification-service", started).count(sender["name"])
                        > email_calls_before
                    )
                    data = result.json()["data"]
                    message_ids.append(data["id"])
                    assert data["senderId"] == sender["id"]
                    assert (
                        count(
                            "message", "messages", f"id={data['id']} AND content={literal(content)}"
                        )
                        == 1
                    )
                    assert (
                        sockets.call("wait", client=target, event="receive_message", id=data["id"])[
                            "payload"
                        ]
                        == data
                    )
                history = client.get(f"/messages/{b['id']}", headers=a["headers"]).json()["data"]
                assert [r["id"] for r in history] == message_ids
                contacts = client.get("/messages/contacts", headers=a["headers"]).json()["data"]
                assert len(contacts) == 1 and contacts[0]["user"]["fullName"] == b["name"]
                assert sockets.call("events", client="c")["events"] == []
                passed(
                    "L-N: real JWT messages -> MySQL/Auth/mock email/events; "
                    "both-direction history and User contacts"
                )
                sockets.call("disconnect", client="b")
                sockets.call(
                    "connect",
                    client="b",
                    url=BASE_URL,
                    userId=b["id"],
                    transports=["polling", "websocket"],
                    upgrade=True,
                )
                rejoin = client.post(
                    "/messages",
                    headers=a["headers"],
                    json={"receiverId": b["id"], "content": marker + " reconnect"},
                ).json()["data"]
                assert (
                    sockets.call("wait", client="b", event="receive_message", id=rejoin["id"])[
                        "payload"
                    ]
                    == rejoin
                )
                passed("reconnect: explicit room rejoin delivers subsequent real message")
                for owner in (b, c):
                    assert (
                        client.post(
                            "/messages/notifications",
                            json={"receiverId": owner["id"], "title": marker, "message": marker},
                        ).status_code
                        == 200
                    )
                other_before = scalar(
                    "message", f"SELECT isRead FROM message_db.notifications WHERE userId={c['id']}"
                )
                assert client.put(
                    "/messages/notifications/read-all", headers=b["headers"]
                ).json() == {"success": True}
                assert (
                    scalar(
                        "message",
                        f"SELECT isRead FROM message_db.notifications WHERE userId={c['id']}",
                    )
                    == other_before
                    == "0"
                )
                # Boundary fixture is owned by the newly registered account. Use
                # distinct timestamps so newest-first is checked without tie rules.
                values = ",".join(
                    f"({a['id']},{literal(marker)},{literal(marker + str(index))},0,"
                    f"DATE_ADD('2027-01-01',INTERVAL {index} SECOND),'2027-01-01')"
                    for index in range(53)
                )
                select(
                    "message",
                    "INSERT INTO message_db.notifications "
                    "(userId,title,message,isRead,createdAt,updatedAt) VALUES " + values,
                )
                listing = client.get("/messages/notifications", headers=a["headers"]).json()["data"]
                assert len(listing) == 50 and all(r["userId"] == a["id"] for r in listing)
                assert [r["createdAt"] for r in listing] == sorted(
                    [r["createdAt"] for r in listing], reverse=True
                )
                assert (
                    client.put("/messages/notifications/read-all", headers=a["headers"]).status_code
                    == 200
                )
                passed(
                    "P-Q: notification list reaches static route; newest-first/own/max50; "
                    "read-all ownership"
                )
                assert (
                    client.post(
                        "/favorites/toggle", headers=b["headers"], json={"postId": pid}
                    ).status_code
                    == 201
                )
                assert client.delete(f"/posts/{pid}", headers=a["headers"]).status_code == 200
                wait_for(
                    lambda: (
                        scalar(
                            "search",
                            "SELECT status FROM phase7_search_e2e.searchindices "
                            f"WHERE postId={pid}",
                        )
                        == "deleted"
                    )
                )
                assert (
                    count("post", "posts", f"id={pid}")
                    == count("post", "images", f"postId={pid}")
                    == 0
                )
                assert client.get("/favorites/my-favorites", headers=b["headers"]).json() == []
                assert (
                    client.get(url).content == BODY
                )  # established owner-delete keeps physical bytes
                passed(
                    "R: owner delete removes Post/images, marks Search deleted, "
                    "Favorite skips missing Post, file retained"
                )
            assert client.post("/notifications/email", json={}).json() == {
                "message": "Email queued (Mock)",
                "mock": True,
            }
            for label, path in (
                ("posts", "/posts"),
                ("search", "/search"),
                ("favorites", "/favorites/my-favorites"),
                ("contacts", "/messages/contacts"),
            ):
                tick = time.monotonic()
                assert client.get(path, headers=a["headers"]).status_code == 200
                timings[label] = round((time.monotonic() - tick) * 1000, 2)
            logs = private_logs("notification-service", started) + private_logs(
                "message-service", started
            )
            assert a["name"] in logs and b["name"] in logs
            assert all(value not in logs for value in private)
            passed("email/mock/request-ID privacy and five latency smoke endpoints")
        finally:
            if posts:
                time.sleep(8)  # bounded Post side effects settle before exact ownership cleanup
            if safe:
                ids = ",".join(map(str, safe))
                for rid in reviews:
                    select(
                        "review",
                        f"DELETE FROM review_db.reviews WHERE id={rid} "
                        f"AND reviewerId IN ({ids}) AND comment LIKE {literal(marker + '%')}",
                    )
                for pid in posts:
                    assert count(
                        "post",
                        "posts",
                        f"id={pid} AND title={literal(marker)} AND userId IN ({ids})",
                    ) in (0, 1)
                    select(
                        "post",
                        f"USE post_db; DELETE i FROM post_db.images i "
                        "JOIN post_db.posts p ON p.id=i.postId "
                        f"WHERE p.id={pid} AND p.title={literal(marker)} "
                        f"AND p.userId IN ({ids})",
                    )
                    select(
                        "post",
                        f"DELETE FROM post_db.posts WHERE id={pid} AND title={literal(marker)} "
                        f"AND userId IN ({ids})",
                    )
                    select(
                        "search",
                        f"DELETE FROM phase7_search_e2e.searchindices WHERE postId={pid} "
                        f"AND title={literal(marker)}",
                    )
                select("favorite", f"DELETE FROM favorite_db.favorites WHERE userId IN ({ids})")
                select(
                    "message",
                    f"DELETE FROM message_db.messages WHERE (senderId IN ({ids}) "
                    f"OR receiverId IN ({ids})) AND content LIKE {literal(marker + '%')}",
                )
                select("message", f"DELETE FROM message_db.notifications WHERE userId IN ({ids})")
                select(
                    "user",
                    f"DELETE FROM user_db.userprofiles WHERE authId IN ({ids}) "
                    f"AND (fullName LIKE {literal(marker + '%')} OR fullName IS NULL)",
                )
            for row in accounts:
                select(
                    "auth",
                    f"DELETE FROM auth_db.users WHERE id={row['id']} "
                    f"AND username={literal(row['name'])} AND email={literal(row['email'])}",
                )
            current = inventory()
            owned = {name: info for name, info in current.items() if marker in name}
            assert not set(owned).intersection(baseline_uploads)
            for name, info in owned.items():
                assert re.fullmatch(r"\d+-" + marker + r"_(post|review)\.png", name)
                assert info["sha256"] == hashlib.sha256(BODY).hexdigest()
                script = (
                    f"import pathlib,hashlib; p=pathlib.Path('/app/uploads')/{name!r};"
                    "assert p.parent==pathlib.Path('/app/uploads') and not p.is_symlink();"
                    f"assert hashlib.sha256(p.read_bytes()).hexdigest()=={info['sha256']!r};"
                    "p.unlink()"
                )
                command(["docker", "exec", "post-service", "python", "-c", script])
            assert inventory() == baseline_uploads
            assert scalar("search", "SELECT COUNT(*) FROM phase7_search_e2e.searchindices") == "0"
            passed(
                "S: only journal-owned synthetic records/files cleaned; all original uploads intact"
            )
            (ARTIFACTS / "e2e-checks.json").write_text(
                json.dumps(checks, indent=2), encoding="utf-8"
            )
            (ARTIFACTS / "latency-ms.json").write_text(
                json.dumps(timings, indent=2), encoding="utf-8"
            )


@pytest.mark.parametrize("endpoint", ENDPOINTS, ids=lambda e: e["id"])
def test_contract_route_method_alias(endpoint):
    # Resolve the actual Django URL and method; make a safe public GET routing probe.
    path = re.sub(r":[A-Za-z][A-Za-z0-9]*", "999999999", endpoint["service_path"])
    method = endpoint["method"].lower()
    script = (
        "import os,django; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings'); "
        "django.setup();"
        "from django.urls import resolve;"
        f" view=resolve({path!r}).func; assert hasattr(view.view_class,{method!r})"
    )
    command(["docker", "exec", endpoint["service"], "python", "-c", script])
    with httpx.Client(timeout=40, trust_env=False) as client:
        for public in [endpoint["gateway_path"], *endpoint.get("aliases", [])]:
            public = re.sub(r":[A-Za-z][A-Za-z0-9]*", "999999999", public)
            response = client.get(BASE_URL + public)
            assert response.status_code in {200, 400, 401, 403, 404, 405, 500}
            assert response.headers.get("content-type", "").startswith("application/json")
            assert "Traceback" not in response.text and "Cannot GET" not in response.text
            assert not response.is_redirect


@pytest.mark.parametrize("service", SERVICES)
def test_health_ready_openapi(service):
    port = SERVICES[service]
    paths = (
        ["/health", "/ready", "/docs", "/openapi.json"]
        if service == "api-gateway"
        else ["/health", "/ready", "/docs/", "/schema/"]
    )
    script = (
        "import urllib.request;"
        f" paths={paths!r};\nfor path in paths:\n"
        f" assert urllib.request.urlopen('http://127.0.0.1:{port}'+path,timeout=10).status==200"
    )
    command(["docker", "exec", service, "python", "-c", script])
