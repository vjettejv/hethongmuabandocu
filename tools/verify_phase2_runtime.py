"""Safe hybrid E2E: only owned synthetic account/profile rows may be removed."""

import json
import secrets
import uuid
from pathlib import Path

import httpx
from verify_runtime import select, snapshot

ROOT = Path(__file__).resolve().parents[1]


def literal(value):
    return "CONVERT(0x" + value.encode().hex() + " USING utf8mb4)"


def main():
    before = json.loads((ROOT / ".artifacts/phase2/db-before.json").read_text())
    username = "phase2-" + uuid.uuid4().hex
    email = username + "@example.invalid"
    password = secrets.token_urlsafe(32)
    owned_id = None
    profile_slot_was_empty = False
    with httpx.Client(base_url="http://127.0.0.1:3000", timeout=30, trust_env=False) as client:
        try:
            for path in ["/health", "/ready", "/posts", "/categories"]:
                response = client.get(path)
                assert response.status_code == 200, f"Smoke failed: {path}"
            print("PASS: Gateway health/ready and real Node Post/Category reads")
            response = client.post(
                "/auth/register",
                json={
                    "username": username,
                    "email": email,
                    "password": password,
                },
                headers={"X-Request-ID": "phase2-e2e"},
            )
            assert response.status_code == 201, "Register failed"
            owned_id = response.json()["userId"]
            assert isinstance(owned_id, int)
            (ROOT / ".artifacts/phase2/e2e-owned.json").write_text(
                json.dumps(
                    {
                        "id": owned_id,
                        "username": username,
                        "email": email,
                    }
                )
            )
            condition = f"id={owned_id} AND username={literal(username)} AND email={literal(email)}"
            assert (
                select("auth", f"SELECT COUNT(*) FROM auth_db.users WHERE {condition}").strip()
                == "1"
            )
            # Never let the legacy User upsert overwrite a pre-existing profile.
            assert (
                select(
                    "user", f"SELECT COUNT(*) FROM user_db.userprofiles WHERE authId={owned_id}"
                ).strip()
                == "0"
            )
            profile_slot_was_empty = True
            print("PASS: Register through FastAPI -> Django -> Node Notification mock")
            otp = select("auth", f"SELECT otp FROM auth_db.users WHERE {condition}").strip()
            response = client.post("/auth/verify-otp", json={"email": email, "otp": otp})
            assert response.status_code == 200, "OTP verification failed"
            assert (
                select(
                    "auth",
                    f"SELECT isVerified=1 AND otp IS NULL FROM auth_db.users WHERE {condition}",
                ).strip()
                == "1"
            )
            print("PASS: Verify OTP and persist verified/cleared OTP state")
            response = client.post("/auth/login", json={"username": username, "password": password})
            assert response.status_code == 200, "Login failed"
            result = response.json()
            assert set(result["user"]) == {"id", "username", "email", "roleId"}
            print("PASS: Login returns legacy token/user envelope")
            authorization = {"Authorization": "Bearer " + result["token"]}
            verified = client.post("/auth/verify", headers=authorization)
            assert verified.status_code == 200
            claims = verified.json()["user"]
            assert claims["id"] == owned_id and claims["exp"] - claims["iat"] == 86400
            profile = client.get("/users/me", headers=authorization)
            assert profile.status_code == 200 and profile.json().get("authId") == owned_id
            assert profile.json()["fullName"] == username
            print("PASS: Python-issued JWT accepted by protected Node User /me through Gateway")
            projection = client.get(f"/auth/{owned_id}")
            assert set(projection.json()) == {"id", "username", "email", "roleId"}
            print("PASS: Public Auth user projection excludes password and OTP")
        finally:
            if owned_id is not None:
                if profile_slot_was_empty:
                    select(
                        "user",
                        f"DELETE FROM user_db.userprofiles WHERE authId={owned_id} "
                        f"AND fullName={literal(username)}",
                    )
                select(
                    "auth",
                    f"DELETE FROM auth_db.users WHERE id={owned_id} "
                    f"AND username={literal(username)} AND email={literal(email)}",
                )
                print("Removed only owned synthetic E2E account/profile; auto-increment untouched")
    assert snapshot() == before, "Legacy schema or row counts differ from baseline"
    print("PASS: all eight legacy schemas and row counts match Phase 2 starting snapshot")


if __name__ == "__main__":
    main()
