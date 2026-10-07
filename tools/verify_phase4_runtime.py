"""Canonical Post/Gateway/Favorite/uploads E2E with isolated Node side effects."""

import hashlib
import json
import re
import secrets
import time
import uuid
from pathlib import Path
from urllib.parse import quote

import httpx
from verify_phase4_uploads import inventory
from verify_runtime import command, select, snapshot

ROOT = Path(__file__).resolve().parents[1]


def literal(value):
    return "CONVERT(0x" + value.encode().hex() + " USING utf8mb4)"


def wait_for(predicate):
    deadline = time.monotonic() + 12
    while not predicate():
        if time.monotonic() >= deadline:
            raise AssertionError("Synthetic side effect missing")
        time.sleep(0.1)


def review_file(name, *, content=None, remove=False):
    script = """
const fs=require('fs'),crypto=require('crypto');
const p=JSON.parse(fs.readFileSync(0,'utf8'));
const owned=/^(?:[0-9]+-)?phase4_test_[a-f0-9]+(?:_[a-z]+)?\\.bin$/;
if(!owned.test(p.name))throw Error('Unowned name');
const target='/app/uploads/'+p.name;
if(p.content!==null)fs.writeFileSync(target,Buffer.from(p.content,'hex'),{flag:'wx'});
const bytes=fs.readFileSync(target);
if(p.remove)fs.unlinkSync(target);
process.stdout.write(crypto.createHash('sha256').update(bytes).digest('hex'));
"""
    import subprocess

    result = subprocess.run(
        ["docker", "exec", "-i", "review-service", "node", "-e", script],
        input=json.dumps(
            {
                "name": name,
                "content": content.hex() if content is not None else None,
                "remove": remove,
            }
        ),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )
    if result.returncode:
        raise RuntimeError("Owned Review/shared-upload operation failed")
    return result.stdout.strip()


def main():
    baseline = json.loads((ROOT / ".artifacts/phase4/db-before.json").read_text())
    files_before = json.loads((ROOT / ".artifacts/phase4/uploads-before.json").read_text())
    # Refuse accidental writes to real Search/Message (next Post ID is occupied in Search).
    config = json.loads(command(["docker", "inspect", "post-service"]))[0]
    environment = dict(item.split("=", 1) for item in config["Config"]["Env"] if "=" in item)
    assert environment["SEARCH_SERVICE_URL"] == "http://dependencies-python:3010"
    assert environment["MESSAGE_SERVICE_URL"] == "http://dependencies-python:3010"
    notification = json.loads(command(["docker", "inspect", "notification-service"]))[0]
    notification_env = dict(
        item.split("=", 1) for item in notification["Config"]["Env"] if "=" in item
    )
    assert notification_env.get("MOCK_EMAIL") == "true", "Runtime E2E requires mock email"
    for service, port in [
        ("api-gateway", 3000),
        ("auth-service", 3001),
        ("user-service", 3002),
        ("post-service", 3003),
        ("category-service", 3004),
    ]:
        probe = (
            "import json,urllib.request;\n"
            "for path in ['/health','/ready']:\n"
            f" with urllib.request.urlopen('http://127.0.0.1:{port}'+path,timeout=8) as r:\n"
            "  data=json.load(r); assert r.status==200\n"
            "  if path=='/ready' and 'database' in data: assert data['database']=='connected'\n"
        )
        command(["docker", "exec", service, "python", "-c", probe])
    print("PASS: five canonical Python services healthy and ready")
    marker = "phase4_test_" + uuid.uuid4().hex
    email = marker + "@example.invalid"
    password = secrets.token_urlsafe(32)
    account_id = post_id = None
    profile_empty = favorite_empty = False
    owned_files = {}
    with httpx.Client(base_url="http://127.0.0.1:3000", timeout=40, trust_env=False) as client:
        try:
            response = client.post(
                "/auth/register",
                json={
                    "username": marker,
                    "email": email,
                    "password": password,
                },
            )
            assert response.status_code == 201
            account_id = response.json()["userId"]
            condition = f"id={account_id} AND username={literal(marker)} AND email={literal(email)}"
            profile_empty = (
                select(
                    "user", f"SELECT COUNT(*) FROM user_db.userprofiles WHERE authId={account_id}"
                ).strip()
                == "0"
            )
            favorite_empty = (
                select(
                    "favorite",
                    f"SELECT COUNT(*) FROM favorite_db.favorites WHERE userId={account_id}",
                ).strip()
                == "0"
            )
            assert profile_empty and favorite_empty, (
                "Synthetic identity has existing dependent rows"
            )
            otp = select("auth", f"SELECT otp FROM auth_db.users WHERE {condition}").strip()
            assert (
                client.post("/auth/verify-otp", json={"email": email, "otp": otp}).status_code
                == 200
            )
            login = client.post("/auth/login", json={"email": email, "password": password})
            assert login.status_code == 200
            auth = {
                "Authorization": "Bearer " + login.json()["token"],
                "X-Request-ID": "phase4-runtime",
            }
            assert client.get("/users/me", headers=auth).json()["authId"] == account_id
            print("PASS: Gateway -> Django Auth login/JWT -> Django User profile")
            categories = client.get("/categories").json()
            category = categories[0]
            content = bytes(range(256)) * 2048
            second = b"phase4-second\x00\xff"
            response = client.post(
                "/posts",
                headers=auth,
                files=[
                    ("categoryId", (None, str(category["id"]))),
                    ("title", (None, marker)),
                    ("price", (None, "123.45")),
                    ("description", (None, "")),
                    ("condition", (None, "legacy-custom")),
                    ("userId", (None, "999999999")),
                    ("images", (marker + "_first.bin", content, "application/octet-stream")),
                    ("images", (marker + "_second.bin", second, "application/octet-stream")),
                ],
            )
            assert response.status_code == 201, "Canonical Post create failed"
            raw = response.json()["post"]
            post_id = raw["id"]
            assert raw["userId"] == account_id and raw["price"] == "123.45"
            assert raw["status"] == "available" and "Images" not in raw and "Category" not in raw
            detail = client.get(f"/posts/{post_id}").json()
            assert detail["price"] == 123.45 and detail["Category"] == category
            assert len(detail["Images"]) == 2 and detail["description"] == ""
            for image, body in zip(detail["Images"], [content, second], strict=True):
                name = image["imageUrl"].removeprefix("/uploads/")
                assert re.fullmatch(r"\d+-" + marker + r"_(first|second)\.bin", name)
                digest = hashlib.sha256(body).hexdigest()
                owned_files[name] = digest
                assert client.get(image["imageUrl"]).content == body
                assert review_file(name) == digest
            assert client.get("/posts", params={"keyword": marker}).json()[0]["id"] == post_id
            assert client.get("/posts/my-posts", headers=auth).json()[0]["id"] == post_id
            assert (
                select(
                    "post", f"SELECT COUNT(*) FROM post_db.images WHERE postId={post_id}"
                ).strip()
                == "2"
            )
            print(
                "PASS: canonical multipart create, numeric query price, Images/Category, "
                "shared Review bytes"
            )
            wait_for(
                lambda: (
                    select(
                        "search",
                        f"SELECT status FROM phase4_search_python.searchindices "
                        f"WHERE postId={post_id} AND title={literal(marker)}",
                    ).strip()
                    == "available"
                )
            )
            print("PASS: create -> real Node Search clone, available remains hidden")
            assert (
                client.post("/favorites/toggle", headers=auth, json={"postId": post_id}).status_code
                == 201
            )
            hydrated = client.get("/favorites/my-favorites", headers=auth).json()
            assert len(hydrated) == 1 and hydrated[0] == detail
            print("PASS: canonical Node Favorite -> canonical Django Post hydration")
            assert (
                client.put(
                    f"/admin/posts/{post_id}", headers=auth, json={"status": "approved"}
                ).status_code
                == 200
            )
            wait_for(
                lambda: (
                    select(
                        "search",
                        f"SELECT status FROM phase4_search_python.searchindices "
                        f"WHERE postId={post_id} AND title={literal(marker)}",
                    ).strip()
                    == "approved"
                )
            )
            wait_for(
                lambda: (
                    select(
                        "message",
                        "SELECT COUNT(*) FROM phase4_message_python.notifications "
                        f"WHERE userId={account_id}",
                    ).strip()
                    == "1"
                )
            )
            assert (
                client.put(
                    f"/posts/admin/posts/{post_id}", headers=auth, json={"status": "rejected"}
                ).status_code
                == 200
            )
            wait_for(
                lambda: (
                    select(
                        "message",
                        "SELECT COUNT(*) FROM phase4_message_python.notifications "
                        f"WHERE userId={account_id}",
                    ).strip()
                    == "2"
                )
            )
            print(
                "PASS: moderation canonical/alias -> Node Search + Node Message clones; "
                "no real realtime recipients"
            )
            assert client.delete(f"/posts/{post_id}", headers=auth).json() == {
                "message": "Deleted successfully"
            }
            wait_for(
                lambda: (
                    select(
                        "search",
                        f"SELECT status FROM phase4_search_python.searchindices "
                        f"WHERE postId={post_id} AND title={literal(marker)}",
                    ).strip()
                    == "deleted"
                )
            )
            assert client.get(f"/posts/{post_id}").status_code == 404
            assert client.get("/favorites/my-favorites", headers=auth).json() == []
            for name, digest in owned_files.items():
                assert review_file(name) == digest  # Owner delete leaves physical files.
            print(
                "PASS: owner delete removes metadata, syncs deleted, keeps files, "
                "Favorite skips missing"
            )
            prewritten = marker + "_existing.bin"
            binary = b"phase4-prewritten\x00\xff"
            digest = hashlib.sha256(binary).hexdigest()
            assert review_file(prewritten, content=binary) == digest
            owned_files[prewritten] = digest
            assert client.get("/uploads/" + prewritten).content == binary
            assert (
                client.get("/uploads/" + prewritten, headers={"Range": "bytes=0-5"}).content
                == binary[:6]
            )
            existing = next(
                name
                for name, item in files_before.items()
                if "sha256" in item and all(not part.startswith(".") for part in Path(name).parts)
            )
            response = client.get("/uploads/" + quote(existing, safe="/"))
            assert response.status_code == 200
            assert hashlib.sha256(response.content).hexdigest() == files_before[existing]["sha256"]
            print(
                "PASS: synthetic prewritten and actual pre-existing shared upload via Gateway; "
                "filenames withheld"
            )
        finally:
            if post_id is not None:
                # Guard every live cleanup by this run's ID + identity/title.
                condition_post = f"id={post_id} AND userId={account_id} AND title={literal(marker)}"
                select(
                    "post",
                    "START TRANSACTION; DELETE FROM post_db.images "
                    f"WHERE postId={post_id} AND postId IN (SELECT id FROM post_db.posts "
                    f"WHERE {condition_post});"
                    f"DELETE FROM post_db.posts WHERE {condition_post}; COMMIT",
                )
                select(
                    "search",
                    f"DELETE FROM phase4_search_python.searchindices WHERE postId={post_id} "
                    f"AND title={literal(marker)}",
                )
                if favorite_empty:
                    select(
                        "favorite",
                        f"DELETE FROM favorite_db.favorites WHERE userId={account_id} "
                        f"AND postId={post_id}",
                    )
            if account_id is not None:
                select(
                    "message",
                    f"DELETE FROM phase4_message_python.notifications WHERE userId={account_id} "
                    "AND message IN ("
                    + literal(f'Bài viết "{marker}" của bạn đã được hiển thị trên chợ.')
                    + ","
                    + literal(f'Bài viết "{marker}" của bạn đã bị từ chối duyệt.')
                    + ")",
                )
                if profile_empty:
                    select(
                        "user",
                        f"DELETE FROM user_db.userprofiles WHERE authId={account_id} "
                        f"AND fullName={literal(marker)}",
                    )
                select(
                    "auth",
                    f"DELETE FROM auth_db.users WHERE id={account_id} "
                    f"AND username={literal(marker)} AND email={literal(email)}",
                )
            for name, digest in owned_files.items():
                assert review_file(name, remove=True) == digest
            print(
                f"Cleanup: owned synthetic records and {len(owned_files)} shared files removed; "
                "no ID reset"
            )
    assert snapshot() == baseline, "Legacy schema/count changed"
    assert inventory() == files_before, "Legacy uploads changed"
    print("PASS: eight legacy schema/count snapshots and all 46 upload entries unchanged")


if __name__ == "__main__":
    main()
