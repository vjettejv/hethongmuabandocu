"""Real hybrid E2E, with guarded cleanup of only this run's synthetic records."""

import json
import secrets
import uuid
from pathlib import Path

import httpx
from verify_phase2_runtime import literal
from verify_runtime import command, select, snapshot

ROOT = Path(__file__).resolve().parents[1]


def main():
    before = json.loads((ROOT / ".artifacts/phase3/db-before.json").read_text())
    username = "phase3_test_" + uuid.uuid4().hex
    email = username + "@example.invalid"
    password = secrets.token_urlsafe(32)
    account_id = category_id = None
    profile_slot_empty = False
    for service, port in [("user-service", 3002), ("category-service", 3004)]:
        probe = (
            "import json,urllib.request; "
            f"base='http://127.0.0.1:{port}'; "
            "\nfor path in ['/health','/ready']:\n"
            " with urllib.request.urlopen(base+path,timeout=8) as r:\n"
            "  data=json.load(r); assert r.status==200\n"
            "  if path=='/ready': assert data['database']=='connected'\n"
        )
        command(["docker", "exec", service, "python", "-c", probe])
    print("PASS: Django User/Category health and read-only DB readiness")
    with httpx.Client(base_url="http://127.0.0.1:3000", timeout=30, trust_env=False) as client:
        try:
            response = client.post(
                "/auth/register", json={"username": username, "email": email, "password": password}
            )
            assert response.status_code == 201, "Register failed"
            account_id = response.json()["userId"]
            assert isinstance(account_id, int)
            condition = (
                f"id={account_id} AND username={literal(username)} AND email={literal(email)}"
            )
            assert (
                select("auth", f"SELECT COUNT(*) FROM auth_db.users WHERE {condition}").strip()
                == "1"
            )
            assert (
                select(
                    "user", f"SELECT COUNT(*) FROM user_db.userprofiles WHERE authId={account_id}"
                ).strip()
                == "0"
            ), "Pre-existing profile slot"
            profile_slot_empty = True
            print("PASS: Register through Gateway -> Django Auth -> Node Notification mock")
            otp = select("auth", f"SELECT otp FROM auth_db.users WHERE {condition}").strip()
            response = client.post("/auth/verify-otp", json={"email": email, "otp": otp})
            assert response.status_code == 200
            assert (
                select(
                    "auth",
                    f"SELECT isVerified=1 AND otp IS NULL FROM auth_db.users WHERE {condition}",
                ).strip()
                == "1"
            )
            public_profile = client.get(f"/users/{account_id}")
            assert public_profile.status_code == 200
            assert public_profile.json()["authId"] == account_id
            assert public_profile.json()["fullName"] == username
            print("PASS: Verify OTP -> Django User PUT -> profile created in user_db")
            login = client.post("/auth/login", json={"email": email, "password": password})
            assert login.status_code == 200
            result = login.json()
            assert set(result) == {"token", "user"}
            authorization = {"Authorization": "Bearer " + result["token"]}
            verified = client.post("/auth/verify", headers=authorization)
            assert verified.status_code == 200
            claims = verified.json()["user"]
            assert claims["id"] == account_id and claims["exp"] - claims["iat"] == 86400
            me = client.get("/users/me", headers=authorization)
            assert me.status_code == 200 and me.json() == public_profile.json()
            update = client.put(
                "/users/me",
                headers=authorization,
                json={"phone": "", "avatar": None, "authId": 999999},
            )
            assert update.status_code == 200 and update.json()["authId"] == account_id
            assert update.json()["fullName"] == username and update.json()["phone"] == ""
            projection = client.get(f"/auth/{account_id}")
            assert set(projection.json()) == {"id", "username", "email", "roleId"}
            print("PASS: Login/Python JWT -> Django User /me and identity-safe partial update")

            created = client.post("/admin/categories", json={"name": username, "description": None})
            assert created.status_code == 201 and set(created.json()) == {"data"}
            category_id = created.json()["data"]["id"]
            listed = client.get("/categories")
            assert listed.status_code == 200 and isinstance(listed.json(), list)
            assert any(
                row["id"] == category_id and row["name"] == username for row in listed.json()
            )
            print("PASS: Gateway -> Django Category admin create/raw list with owned fixture")
            category_map = {row["id"]: row for row in listed.json()}
            posts = client.get("/posts")
            assert posts.status_code == 200 and isinstance(posts.json(), list) and posts.json()
            existing = next(row for row in posts.json() if row["categoryId"] in category_map)
            assert existing["Category"] == category_map[existing["categoryId"]]
            detail = client.get(f"/posts/{existing['id']}")
            assert detail.status_code == 200 and detail.json()["Category"] == existing["Category"]
            print("PASS: real Node Post list/detail enrich from canonical Django Category")
        finally:
            if category_id is not None:
                select(
                    "category",
                    f"DELETE FROM category_db.categories WHERE id={category_id} "
                    f"AND name={literal(username)} AND description IS NULL",
                )
            if account_id is not None:
                if profile_slot_empty:
                    select(
                        "user",
                        f"DELETE FROM user_db.userprofiles WHERE authId={account_id} "
                        f"AND fullName={literal(username)}",
                    )
                select(
                    "auth",
                    f"DELETE FROM auth_db.users WHERE id={account_id} "
                    f"AND username={literal(username)} AND email={literal(email)}",
                )
            print("Cleanup: removed only owned synthetic records; no auto-increment reset")
    assert snapshot() == before, "Legacy schema or row counts differ from Phase 3 baseline"
    print("PASS: all eight schemas and row counts match Phase 3 starting snapshot")


if __name__ == "__main__":
    main()
