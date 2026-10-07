"""Guarded canonical E2E: real hybrid services, isolated Search/Message effects."""

import hashlib
import json
import re
import secrets
import subprocess
import time
import uuid
from pathlib import Path
from urllib.parse import quote

import httpx
from verify_phase4_runtime import literal
from verify_phase4_uploads import inventory
from verify_runtime import command, select, snapshot

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / ".artifacts/phase5"


def environment(service):
    container = json.loads(command(["docker", "inspect", service]))[0]
    return dict(item.split("=", 1) for item in container["Config"]["Env"] if "=" in item)


def wait_for(check):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if check():
            return
        time.sleep(0.1)
    raise AssertionError("Synthetic side effect missing")


def owned_file(marker, name, digest, remove=False):
    assert re.fullmatch(r"\d+-" + re.escape(marker) + r"_[a-z]+\.bin", name)
    script = """
import sys,json,pathlib,hashlib
p=json.load(sys.stdin); target=pathlib.Path('/app/uploads')/p['name']
assert not target.is_symlink()
assert hashlib.sha256(target.read_bytes()).hexdigest()==p['digest']
if p['remove']: target.unlink()
print('PASS')
"""
    result = subprocess.run(
        ["docker", "exec", "-i", "post-service", "python", "-c", script],
        input=json.dumps({"name": name, "digest": digest, "remove": remove}),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, "Owned file hash/cleanup check failed"


def main():
    baseline = json.loads((ARTIFACTS / "db-before.json").read_text(encoding="utf-8-sig"))
    files_before = json.loads((ARTIFACTS / "uploads-before.json").read_text())
    assert environment("search-service")["DB_NAME"] == "phase5_search_e2e"
    assert environment("post-service")["SEARCH_SERVICE_URL"] == "http://search-service:3008"
    assert environment("post-service")["MESSAGE_SERVICE_URL"] == "http://dependencies-phase5:3010"
    assert environment("notification-service").get("MOCK_EMAIL") == "true"
    assert "phase5_search_e2e" in json.loads((ARTIFACTS / "test-databases.json").read_text())
    assert select("search", "SELECT COUNT(*) FROM phase5_search_e2e.searchindices").strip() == "0"
    marker = "phase5_test_" + uuid.uuid4().hex
    email, password = marker + "@example.invalid", secrets.token_urlsafe(32)
    account_id = post_id = review_id = None
    profile_empty = favorite_empty = review_empty = False
    owned_files = {}
    created_files = 0

    def track(url, body):
        nonlocal created_files
        name = url.removeprefix("/uploads/")
        assert name not in files_before
        owned_files[name] = hashlib.sha256(body).hexdigest()
        created_files += 1
        journal()
        owned_file(marker, name, owned_files[name])

    def journal():
        # Recovery metadata contains only owned IDs and names, never credentials.
        (ARTIFACTS / "runtime-owned.json").write_text(
            json.dumps(
                {
                    "marker": marker,
                    "accountId": account_id,
                    "postId": post_id,
                    "reviewId": review_id,
                    "files": owned_files,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    with httpx.Client(base_url="http://127.0.0.1:3000", timeout=40, trust_env=False) as client:
        try:
            result = client.post(
                "/auth/register", json={"username": marker, "email": email, "password": password}
            )
            assert result.status_code == 201
            account_id = result.json()["userId"]
            journal()
            account_guard = (
                f"id={account_id} AND username={literal(marker)} AND email={literal(email)}"
            )
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
            review_empty = (
                select(
                    "review",
                    f"SELECT COUNT(*) FROM review_db.reviews WHERE reviewerId={account_id} "
                    f"OR revieweeId={account_id}",
                ).strip()
                == "0"
            )
            assert profile_empty and favorite_empty and review_empty
            otp = select("auth", f"SELECT otp FROM auth_db.users WHERE {account_guard}").strip()
            assert (
                client.post("/auth/verify-otp", json={"email": email, "otp": otp}).status_code
                == 200
            )
            login = client.post("/auth/login", json={"email": email, "password": password})
            assert login.status_code == 200
            auth = {
                "Authorization": "Bearer " + login.json()["token"],
                "X-Request-ID": "phase5-runtime",
            }
            assert client.get("/users/me", headers=auth).json()["authId"] == account_id
            category = client.get("/categories").json()[0]
            first, second = bytes(range(256)) * 2048, b"phase5-second\x00\xff"
            created = client.post(
                "/posts",
                headers=auth,
                data={
                    "categoryId": str(category["id"]),
                    "title": marker,
                    "price": "123.45",
                    "description": "",
                },
                files=[
                    ("images", (marker + "_first.bin", first)),
                    ("images", (marker + "_second.bin", second)),
                ],
            )
            assert created.status_code == 201
            post_id = created.json()["post"]["id"]
            journal()
            detail = client.get(f"/posts/{post_id}").json()
            assert detail["price"] == 123.45 and detail["Category"] == category
            assert len(detail["Images"]) == 2
            for image, body in zip(detail["Images"], [first, second], strict=True):
                track(image["imageUrl"], body)
                assert client.get(image["imageUrl"]).content == body
            search_guard = f"postId={post_id} AND title={literal(marker)}"
            wait_for(
                lambda: (
                    select(
                        "search",
                        f"SELECT status FROM phase5_search_e2e.searchindices WHERE {search_guard}",
                    ).strip()
                    == "available"
                )
            )
            print(
                "PASS: canonical Auth JWT -> Gateway/Post -> canonical Django Search "
                "DNS; create projection"
            )
            assert client.get("/favorites/my-favorites", headers=auth).json() == []
            assert (
                client.post("/favorites/toggle", headers=auth, json={"postId": post_id}).status_code
                == 201
            )
            assert client.get(f"/favorites/check/{post_id}", headers=auth).json() == {
                "isFavorited": True
            }
            assert client.get("/favorites/my-favorites", headers=auth).json() == [detail]
            assert (
                client.post("/favorites/toggle", headers=auth, json={"postId": post_id}).status_code
                == 200
            )
            assert client.get(f"/favorites/check/{post_id}", headers=auth).json() == {
                "isFavorited": False
            }
            assert (
                client.post("/favorites/toggle", headers=auth, json={"postId": post_id}).status_code
                == 201
            )
            print("PASS: canonical Django Favorite toggle/check/hydration -> Django Post")
            for status in ("approved", "rejected", "approved"):
                assert (
                    client.put(
                        f"/admin/posts/{post_id}", headers=auth, json={"status": status}
                    ).status_code
                    == 200
                )
                wait_for(
                    lambda status=status: (
                        select(
                            "search",
                            f"SELECT status FROM phase5_search_e2e.searchindices WHERE "
                            f"{search_guard}",
                        ).strip()
                        == status
                    )
                )
                results = client.get(
                    "/search",
                    params={
                        "query": marker,
                        "categoryId": str(category["id"]),
                        "minPrice": "123",
                        "maxPrice": "124",
                    },
                ).json()
                if status == "approved":
                    assert len(results) == 1 and results[0]["id"] == results[0]["postId"] == post_id
                    assert results[0]["price"] == "123.45"
                else:
                    assert results == []
            print(
                "PASS: moderation -> Django Search approved/filter/price string/id "
                "alias; Message effects isolated"
            )
            image_a, image_b = b"phase5-review-A\x00\xff", b"phase5-review-B\x80\x00"
            review = client.post(
                "/reviews",
                data={
                    "reviewerId": str(account_id),
                    "revieweeId": str(account_id),
                    "postId": str(post_id),
                    "rating": "5",
                    "comment": marker,
                },
                files={"image": (marker + "_reviewa.bin", image_a)},
            )
            assert review.status_code == 201
            review_id = review.json()["id"]
            journal()
            url_a = review.json()["imageUrl"]
            track(url_a, image_a)
            assert client.get(url_a).content == image_a
            listed = client.get(
                f"/reviews/user/{account_id}", params={"rating": "5", "hasImage": "true"}
            ).json()
            assert len(listed) == 1 and listed[0]["id"] == review_id and listed[0]["rating"] == 5
            replaced = client.put(
                f"/reviews/{review_id}",
                data={"comment": ""},
                files={"image": (marker + "_reviewb.bin", image_b)},
            )
            assert replaced.status_code == 200 and replaced.json()["comment"] == marker
            url_b = replaced.json()["imageUrl"]
            track(url_b, image_b)
            assert client.get(url_a).status_code == 404
            owned_files.pop(url_a.removeprefix("/uploads/"))
            journal()
            assert client.get(url_b).content == image_b
            assert client.get(url_b, headers={"Range": "bytes=1-4"}).content == image_b[1:5]
            assert client.delete(f"/reviews/{review_id}").json() == {
                "message": "Review deleted successfully"
            }
            assert client.get(url_b).status_code == 404
            owned_files.pop(url_b.removeprefix("/uploads/"))
            journal()
            print(
                "PASS: canonical public Review create/filter/truthy "
                "update/replacement/delete -> shared volume -> Post/Gateway bytes"
            )
            assert client.delete(f"/posts/{post_id}", headers=auth).status_code == 200
            wait_for(
                lambda: (
                    select(
                        "search",
                        f"SELECT status FROM phase5_search_e2e.searchindices WHERE {search_guard}",
                    ).strip()
                    == "deleted"
                )
            )
            assert (
                select(
                    "search",
                    f"SELECT imageUrl IS NULL FROM phase5_search_e2e.searchindices WHERE "
                    f"{search_guard}",
                ).strip()
                == "1"
            )
            assert client.get("/favorites/my-favorites", headers=auth).json() == []
            for name, digest in owned_files.items():
                owned_file(marker, name, digest)
            existing = next(
                name
                for name, entry in files_before.items()
                if "sha256" in entry and all(not part.startswith(".") for part in Path(name).parts)
            )
            response = client.get("/uploads/" + quote(existing, safe="/"))
            assert (
                response.status_code == 200
                and hashlib.sha256(response.content).hexdigest() == files_before[existing]["sha256"]
            )
            print(
                "PASS: owner delete -> deleted/null image projection, Favorite "
                "filtering, retained Post files and existing upload hash"
            )
            wait_for(
                lambda: (
                    select(
                        "message",
                        f"SELECT COUNT(*) FROM phase5_message_test.notifications WHERE "
                        f"userId={account_id}",
                    ).strip()
                    == "3"
                )
            )
        finally:
            # Exact ID + UUID guards, no unknown-row/file cleanup or ID reset.
            if review_id is not None and review_empty:
                select(
                    "review",
                    f"DELETE FROM review_db.reviews WHERE id={review_id} AND "
                    f"reviewerId={account_id} AND revieweeId={account_id} AND "
                    f"comment={literal(marker)}",
                )
            if post_id is not None:
                guard = f"id={post_id} AND userId={account_id} AND title={literal(marker)}"
                select(
                    "post",
                    "START TRANSACTION; DELETE FROM post_db.images "
                    + f"WHERE postId={post_id} "
                    + f"AND postId IN (SELECT id FROM post_db.posts WHERE {guard});"
                    + f"DELETE FROM post_db.posts WHERE {guard}; COMMIT",
                )
                select(
                    "search",
                    f"DELETE FROM phase5_search_e2e.searchindices WHERE postId={post_id} "
                    f"AND title={literal(marker)}",
                )
                if favorite_empty:
                    select(
                        "favorite",
                        f"DELETE FROM favorite_db.favorites WHERE userId={account_id} AND "
                        f"postId={post_id}",
                    )
            if account_id is not None:
                approved_message = literal(
                    f'Bài viết "{marker}" của bạn đã được hiển thị trên chợ.'
                )
                rejected_message = literal(f'Bài viết "{marker}" của bạn đã bị từ chối duyệt.')
                select(
                    "message",
                    "DELETE FROM phase5_message_test.notifications "
                    f"WHERE userId={account_id} "
                    f"AND message IN ({approved_message},{rejected_message})",
                )
                if profile_empty:
                    select(
                        "user",
                        f"DELETE FROM user_db.userprofiles WHERE authId={account_id} AND "
                        f"fullName={literal(marker)}",
                    )
                select(
                    "auth",
                    f"DELETE FROM auth_db.users WHERE id={account_id} AND "
                    f"username={literal(marker)} AND email={literal(email)}",
                )
            remaining = inventory()
            for name, digest in owned_files.items():
                if name in remaining:
                    owned_file(marker, name, digest, remove=True)
            owned_files.clear()
            journal()
            print(
                f"Cleanup: {created_files} shared test files created, removed by "
                f"lifecycle/guarded cleanup"
            )
    assert snapshot() == baseline, "Legacy schemas/counts changed"
    assert inventory() == files_before, "Shared uploads changed"
    print("PASS: canonical E2E; all eight schema/counts and all shared upload bytes unchanged")


if __name__ == "__main__":
    main()
