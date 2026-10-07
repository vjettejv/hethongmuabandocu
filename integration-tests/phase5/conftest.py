import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from functools import cache
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from prepare_phase5_tests import CLONES  # noqa: E402
from verify_runtime import select  # noqa: E402

USER = 5100100
BODY = b"phase5-safe-binary\x00\xff\x80" + bytes(range(256))


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
    if result.returncode:
        raise RuntimeError("Fixture docker command failed")
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
    data = json.loads(docker("inspect", container(service)))[0]
    mapping = data["NetworkSettings"]["Ports"][f"{port}/tcp"][0]
    assert mapping["HostIp"] == "127.0.0.1"
    return "http://127.0.0.1:" + mapping["HostPort"]


def headers(kind="valid", user=USER):
    if kind == "missing":
        return {"X-Request-ID": "phase5-test"}
    if kind == "invalid":
        return {"Authorization": "Bearer invalid", "X-Request-ID": "phase5-test"}
    script = (
        "const fs=require('fs'),jwt=require('jsonwebtoken');"
        "const d=JSON.parse(fs.readFileSync(0,'utf8'));"
        "process.stdout.write(jwt.sign({id:d.id,roleId:1},"
        "d.wrong?'phase5-wrong-key':process.env.JWT_SECRET,"
        "{expiresIn:d.expired?-10:'1d'}));"
    )
    token = docker(
        "exec",
        "-i",
        container("favorite-phase5-node"),
        "node",
        "-e",
        script,
        input_data=json.dumps({"id": user, "wrong": kind == "wrong", "expired": kind == "expired"}),
    )
    return {"Authorization": "Bearer " + token, "X-Request-ID": "phase5-test"}


def rows(kind, database, table):
    columns = select(
        kind,
        "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
        f"WHERE TABLE_SCHEMA='{database}' AND TABLE_NAME='{table}' ORDER BY ORDINAL_POSITION",
    ).splitlines()
    pairs = ",".join(f"'{c}',`{c}`" for c in columns)
    return [
        json.loads(line)
        for line in select(
            kind,
            f"SET NAMES utf8mb4; SELECT JSON_OBJECT({pairs}) "
            f"FROM `{database}`.`{table}` ORDER BY 1",
        ).splitlines()
    ]


def files(runtime):
    service = "review-phase5-" + runtime
    script = (
        "const fs=require('fs');"
        "process.stdout.write(JSON.stringify(fs.readdirSync('/app/uploads')))"
        if runtime == "node"
        else "import os,json; print(json.dumps(os.listdir('/app/uploads')))"
    )
    return set(
        json.loads(
            docker(
                "exec",
                container(service),
                "node" if runtime == "node" else "python",
                "-e" if runtime == "node" else "-c",
                script,
            )
        )
    )


def read_file(runtime, url):
    assert url.startswith("/uploads/") and "/" not in url.removeprefix("/uploads/")
    if runtime == "node":
        script = (
            "const fs=require('fs');"
            "process.stdout.write(fs.readFileSync(process.argv[1]).toString('hex'))"
        )
        return bytes.fromhex(
            docker("exec", container("review-phase5-node"), "node", "-e", script, "/app" + url)
        )
    script = "import pathlib,sys; print(pathlib.Path(sys.argv[1]).read_bytes().hex())"
    return bytes.fromhex(
        docker("exec", container("review-phase5-python"), "python", "-c", script, "/app" + url)
    )


def wait_for(check):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        result = check()
        if result:
            return result
        time.sleep(0.1)
    raise AssertionError("Expected asynchronous side effect missing")


@pytest.fixture(scope="session")
def live():
    assert os.environ.get("PHASE5_TEST") == "1", "Start explicit Phase 5 fixtures first"
    owned = json.loads((ROOT / ".artifacts/phase5/test-databases.json").read_text())
    assert {database for _, database, _ in CLONES} <= set(owned)
    urls = {
        svc: {kind: published(f"{svc}-phase5-{kind}", port) for kind in ("node", "python")}
        for svc, port in [("favorite", 3009), ("review", 3007), ("search", 3008)]
    }
    urls.update(
        post=published("post-phase5", 3003),
        gateway=published("gateway-phase5", 3000),
        dependencies=published("dependencies-phase5", 3010),
    )
    with httpx.Client(timeout=30, trust_env=False) as client:
        for svc in ("favorite", "review", "search"):
            for url in urls[svc].values():
                assert client.get(url + "/unknown/probe").status_code == 404
        yield client, urls


@pytest.fixture(autouse=True)
def owned_cleanup(live):
    client, urls = live
    before = {kind: files(kind) for kind in ("node", "python")}

    def clean():
        wait_for(lambda: client.get(urls["dependencies"] + "/__events").json()["pending"] == 0)
        assert client.post(urls["dependencies"] + "/__control", json={}).status_code == 200
        grouped = {}
        for kind, database, tables in CLONES:
            grouped.setdefault(kind, []).extend(
                f"DELETE FROM `{database}`.`{table}`" for table in reversed(tables)
            )
        for kind, statements in grouped.items():
            select(kind, ";".join(statements))

    clean()
    try:
        yield
    finally:
        clean()
        for kind in ("node", "python"):
            current = files(kind)
            assert before[kind] <= current, "Pre-existing fixture file lost"
            new = current - before[kind]
            assert all(re.fullmatch(r"\d+-phase5_test_[^/\\]+", name) for name in new)
            if kind == "node":
                script = (
                    "const fs=require('fs');for(const n of JSON.parse(fs.readFileSync(0,'utf8')))"
                    "fs.unlinkSync('/app/uploads/'+n);"
                )
            else:
                script = (
                    "import sys,json,pathlib;"
                    "[(pathlib.Path('/app/uploads')/n).unlink() for n in json.load(sys.stdin)]"
                )
            docker(
                "exec",
                "-i",
                container("review-phase5-" + kind),
                "node" if kind == "node" else "python",
                "-e" if kind == "node" else "-c",
                script,
                input_data=json.dumps(sorted(new)),
            )
            assert files(kind) == before[kind]


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
                ) < (8 if generated else 0.001)
            elif key == "id" and generated:
                assert isinstance(value, int) and isinstance(right[key], int)
            elif key == "imageUrl" and generated and value:
                assert re.fullmatch(r"/uploads/\d+-phase5_test_[^/]+", value)
                assert re.fullmatch(r"/uploads/\d+-phase5_test_[^/]+", right[key])
                assert value.split("-", 1)[1] == right[key].split("-", 1)[1]
            else:
                compare(value, right[key], generated)
    else:
        assert left == right


def seed_reviews():
    for kind in ("node", "python"):
        select(
            "review",
            f"INSERT INTO phase5_review_{kind}.reviews (id,reviewerId,revieweeId,postId,"
            f"rating,comment,imageUrl,createdAt,updatedAt) VALUES (1,11,{USER},NULL,1,"
            f"'phase5_test alpha',NULL,'2026-01-01','2026-01-01'),(2,12,{USER},8,5,"
            f"'phase5_test beta','/uploads/phase5_test_absent.png','2026-01-03',"
            f"'2026-01-03'),(3,11,{USER},NULL,3,'phase5_test gamma',NULL,'2026-01-02',"
            f"'2026-01-02'),(4,11,{USER + 1},NULL,5,NULL,NULL,'2026-01-04','2026-01-04')",
        )


def seed_search():
    for kind in ("node", "python"):
        select(
            "search",
            f"INSERT INTO phase5_search_{kind}.searchindices (postId,title,description,"
            f"price,categoryId,imageUrl,categoryName,status,createdAt,updatedAt) VALUES "
            f"(1,'phase5_test Alpha','match description',12.50,1,NULL,'One','approved',"
            f"'2026-01-01','2026-01-01'),(2,'phase5_test Beta',NULL,0,2,NULL,'Two',"
            f"'approved','2026-01-03','2026-01-03'),(3,'phase5_test Hidden','match "
            f"description',1.99,1,NULL,'One','available','2026-01-04','2026-01-04'),(4,"
            f"'phase5_test Gamma','match description',20.01,1,NULL,'One','approved',"
            f"'2026-01-02','2026-01-02'),(5,'phase5_test Null',NULL,NULL,3,NULL,NULL,"
            f"'approved','2026-01-05','2026-01-05')",
        )
