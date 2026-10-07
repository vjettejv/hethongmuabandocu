import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import cache
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from phase6_socket import SocketClient  # noqa: E402
from prepare_phase6_tests import CLONES  # noqa: E402
from verify_runtime import select  # noqa: E402

A, B, C = 6100001, 6100002, 6100003


def docker(*args, input_data=None):
    result = subprocess.run(
        ["docker", *args],
        input=input_data,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, "Fixture docker operation failed"
    return result.stdout.strip()


@cache
def container(service):
    identifier = docker(
        "ps",
        "-a",
        "--filter",
        "label=com.docker.compose.project=kientrucpm",
        "--filter",
        f"label=com.docker.compose.service={service}",
        "--format",
        "{{.ID}}",
    )
    assert identifier and "\n" not in identifier
    return identifier


def published(service, port):
    item = json.loads(docker("inspect", container(service)))[0]
    mapping = item["NetworkSettings"]["Ports"][f"{port}/tcp"][0]
    assert mapping["HostIp"] == "127.0.0.1"
    return "http://127.0.0.1:" + mapping["HostPort"]


def headers(kind="valid", user=A):
    result = {"X-Request-ID": "phase6-parity"}
    if kind == "missing":
        return result
    if kind == "invalid":
        return {**result, "Authorization": "Bearer invalid"}
    script = (
        "const fs=require('fs'),jwt=require('jsonwebtoken');"
        "const d=JSON.parse(fs.readFileSync(0,'utf8'));"
        "process.stdout.write(jwt.sign({id:d.id,roleId:1},"
        "d.wrong?'phase6-wrong-key':process.env.JWT_SECRET,"
        "{expiresIn:d.expired?-10:'1d'}));"
    )
    token = docker(
        "exec",
        "-i",
        container("message-phase6-node"),
        "node",
        "-e",
        script,
        input_data=json.dumps({"id": user, "wrong": kind == "wrong", "expired": kind == "expired"}),
    )
    return {**result, "Authorization": "Bearer " + token}


def wait_for(check):
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        value = check()
        if value:
            return value
        time.sleep(0.1)
    raise AssertionError("Expected side effect missing")


def compare(left, right, generated=False):
    assert type(left) is type(right)
    if isinstance(left, list):
        assert len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            compare(a, b, generated)
    elif isinstance(left, dict):
        assert set(left) == set(right)
        for key, value in left.items():
            if key in {"createdAt", "updatedAt"} and value is not None:
                assert value.endswith("Z") and right[key].endswith("Z")
                assert abs(
                    (
                        datetime.fromisoformat(value) - datetime.fromisoformat(right[key])
                    ).total_seconds()
                ) < (12 if generated else 0.001)
            elif key == "id" and generated:
                assert isinstance(value, int) and isinstance(right[key], int)
            else:
                compare(value, right[key], generated)
    else:
        assert left == right


def events(live, runtime):
    client, urls = live
    return client.get(urls["dependencies"][runtime] + "/__events").json()["events"]


def seed_messages():
    for runtime in ("node", "python"):
        select(
            "message",
            f"INSERT INTO phase6_message_{runtime}.messages "
            "(id,senderId,receiverId,content,isRead,createdAt,updatedAt) VALUES "
            f"(1,{A},{B},'first',0,'2026-01-01 01:00:00','2026-01-01 01:00:00'),"
            f"(2,{B},{A},'reply',1,'2026-01-01 02:00:00','2026-01-01 02:00:00'),"
            f"(3,{A},{C},'latest',0,'2026-01-01 03:00:00','2026-01-01 03:00:00'),"
            f"(4,{C},99999999,'unrelated',0,NOW(),NOW())",
        )


@pytest.fixture(scope="session")
def live():
    assert os.environ.get("PHASE6_TEST") == "1"
    owned = json.loads((ROOT / ".artifacts/phase6/test-databases.json").read_text())
    assert {database for _, database, _ in CLONES} <= set(owned)
    urls = {
        "message": {r: published("message-phase6-" + r, 3005) for r in ("node", "python")},
        "dependencies": {
            r: published("dependencies-phase6-" + r, 3011) for r in ("node", "python")
        },
    }
    urls["email"] = {
        mode: {r: published(f"notification-phase6-{r}" + suffix, 3006) for r in ("node", "python")}
        for mode, suffix in [
            ("development", ""),
            ("production-mock", "-production-mock"),
            ("missing-user", "-missing-user"),
            ("smtp", "-smtp"),
        ]
    }
    urls.update(
        gateway=published("gateway-phase6", 3000),
        smtp=published("smtp-phase6", 3012),
        auth=published("auth-phase6", 3001),
        user=published("user-phase6", 3002),
        post=published("post-phase6", 3003),
    )
    # Fresh host-side REST connections avoid the Node fixture's idle-close race
    # during long SQL cleanup. Socket.IO transport connections remain persistent.
    with httpx.Client(
        timeout=30, trust_env=False, limits=httpx.Limits(max_keepalive_connections=0)
    ) as client:
        for r in ("node", "python"):
            assert client.get(urls["message"][r] + "/contacts").status_code == 401
        yield client, urls


@pytest.fixture(autouse=True)
def clean_owned(live):
    client, urls = live

    def clean():
        for url in urls["dependencies"].values():
            wait_for(lambda url=url: client.get(url + "/__events").json()["pending"] == 0)
            assert client.post(url + "/__control", json={}).status_code == 200
        client.post(urls["smtp"] + "/__control", json={})
        grouped = {}
        for kind, database, tables in CLONES:
            assert database.startswith("phase6_")
            grouped.setdefault(kind, []).extend(
                f"DELETE FROM `{database}`.`{table}`" for table in reversed(tables)
            )
        # Different MySQL containers are independent; inspect every cleanup result.
        with ThreadPoolExecutor(max_workers=5) as pool:
            operations = [
                pool.submit(select, kind, ";".join(statements))
                for kind, statements in grouped.items()
            ]
            for operation in operations:
                operation.result()

    clean()
    select(
        "auth",
        "INSERT INTO phase6_auth_test.users "
        "(id,roleId,username,email,password,isVerified,createdAt,updatedAt) VALUES "
        + ",".join(
            f"({i},1,'phase6_{i}','phase6_{i}@example.invalid','synthetic-only',1,NOW(),NOW())"
            for i in (A, B, C)
        ),
    )
    select(
        "user",
        "INSERT INTO phase6_user_test.userprofiles (authId,fullName,createdAt,updatedAt) VALUES "
        + ",".join(f"({i},'Phase6 User {i}',NOW(),NOW())" for i in (A, B)),
    )
    try:
        yield
    finally:
        clean()


@pytest.fixture
def sockets():
    with SocketClient() as client:
        yield client
