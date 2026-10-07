"""Boot immutable Node reference in a separate project and disposable tmpfs database."""

import json
import os
import secrets
import subprocess
import time
from pathlib import Path

import bcrypt
import httpx
from legacy_reference import export
from verify_phase4_runtime import literal
from verify_runtime import command, select

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / ".artifacts/phase7"
COMPOSE = ["docker", "compose", "-f", "docker-compose.phase7.rollback-test.yml"]


def compose(*args):
    result = subprocess.run(
        [*COMPOSE, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=300,
        check=False,
    )
    if result.returncode:
        raise RuntimeError("Isolated recovery Compose operation failed")
    return result.stdout


def sql(container, query):
    result = subprocess.run(
        [
            "docker",
            "exec",
            "-i",
            container,
            "sh",
            "-c",
            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch',
        ],
        input=query,
        text=True,
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, "Rehearsal SQL failed (diagnostics withheld)"


def main():
    directory = ARTIFACTS / "legacy"
    export(directory)
    os.environ["PHASE7_LEGACY_DIR"] = str(directory)
    password = secrets.token_urlsafe(36)
    os.environ["PHASE7_ROLLBACK_PASSWORD"] = password
    checks = []
    try:
        compose("config", "--quiet")
        compose("up", "-d", "db")
        database = compose("ps", "-q", "db").strip()
        for _ in range(60):
            try:
                sql(database, "SELECT 1;")
                break
            except AssertionError:
                time.sleep(1)
        else:
            raise RuntimeError("Isolated database not ready")
        statements = []
        for kind, tables in (
            ("auth", ["users"]),
            ("category", ["categories"]),
            ("post", ["posts", "images"]),
        ):
            statements += [f"CREATE DATABASE {kind}_db; USE {kind}_db;"]
            for table in tables:
                ddl = select(kind, f"SHOW CREATE TABLE {kind}_db.{table}").split("\t", 1)[1]
                statements.append(ddl + ";")
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        statements += [
            "INSERT INTO auth_db.users "
            "(id,username,email,password,roleId,isVerified,createdAt,updatedAt) "
            f"VALUES(1,'phase7_rollback','phase7_rollback@example.invalid',"
            f"{literal(hashed)},1,1,NOW(),NOW());",
            "INSERT INTO category_db.categories(id,name,createdAt,updatedAt) "
            "VALUES(1,'phase7_rollback',NOW(),NOW());",
            "INSERT INTO post_db.posts "
            "(id,userId,categoryId,title,price,status,createdAt,updatedAt) "
            "VALUES(1,1,1,'phase7_rollback',12.34,'approved',NOW(),NOW());",
        ]
        sql(database, "\n".join(statements))
        compose(
            "up",
            "-d",
            "--build",
            "--no-deps",
            "api-gateway",
            "auth-service",
            "post-service",
            "category-service",
        )
        gateway = compose("ps", "-q", "api-gateway").strip()
        row = json.loads(command(["docker", "inspect", gateway]))[0]
        mapping = row["NetworkSettings"]["Ports"]["3000/tcp"][0]
        assert mapping["HostIp"] == "127.0.0.1"
        assert set(row["NetworkSettings"]["Networks"]) == {"phase7-legacy-recovery_default"}
        with httpx.Client(
            base_url="http://127.0.0.1:" + mapping["HostPort"], timeout=15, trust_env=False
        ) as client:
            for _ in range(30):
                try:
                    if client.get("/health").status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(1)
            time.sleep(3)
            assert client.get("/health").text == "Gateway OK"
            checks.append("immutable Node Gateway boot")
            login = client.post(
                "/auth/login",
                json={"email": "phase7_rollback@example.invalid", "password": password},
            )
            assert login.status_code == 200 and login.json()["token"]
            checks.append("Node Auth login with isolated synthetic bcrypt account")
            posts = client.get("/posts")
            assert posts.status_code == 200 and posts.json()[0]["title"] == "phase7_rollback"
            checks.append("Node Post list through Node Gateway")
            categories = client.get("/categories")
            assert (
                categories.status_code == 200 and categories.json()[0]["name"] == "phase7_rollback"
            )
            checks.append("Node Category list through Node Gateway")
        for check in checks:
            print("PASS:", check, flush=True)
        (ARTIFACTS / "rollback-checks.json").write_text(
            json.dumps(checks, indent=2), encoding="utf-8"
        )
    finally:
        compose("down")  # no volumes; own tmpfs only, never canonical project
        print("Isolated rollback processes/network removed; canonical volumes untouched")


if __name__ == "__main__":
    main()
