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
from prepare_phase4_tests import CLONES  # noqa: E402
from verify_runtime import select  # noqa: E402

USER_ID = 4100100
POST_DBS = {runtime: f"phase4_post_{runtime}" for runtime in ("node", "python")}


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
        raise RuntimeError("Docker fixture operation failed")
    return result.stdout.strip()


@cache
def container(service):
    value = docker(
        "ps",
        "-a",
        "--filter",
        "label=com.docker.compose.project=kientrucpm",
        "--filter",
        f"label=com.docker.compose.service={service}",
        "--format",
        "{{.ID}}",
    )
    if not value or "\n" in value:
        raise RuntimeError(f"Expected one fixture container: {service}")
    return value


def published(service, port):
    value = json.loads(docker("inspect", container(service)))[0]
    mapping = value["NetworkSettings"]["Ports"][f"{port}/tcp"][0]
    assert mapping["HostIp"] == "127.0.0.1"
    return "http://127.0.0.1:" + mapping["HostPort"]


def literal(value):
    return "CONVERT(0x" + value.encode().hex() + " USING utf8mb4)"


def signed_token(*, user_id=USER_ID, expired=False, wrong=False):
    script = (
        "const fs=require('fs'),jwt=require('jsonwebtoken');"
        "const p=JSON.parse(fs.readFileSync(0,'utf8'));"
        "process.stdout.write(jwt.sign({id:p.id,roleId:1},p.wrong?'wrong-key':"
        "process.env.JWT_SECRET,{expiresIn:p.expired?-10:'1d'}));"
    )
    return docker(
        "exec",
        "-i",
        container("post-reference"),
        "node",
        "-e",
        script,
        input_data=json.dumps({"id": user_id, "expired": expired, "wrong": wrong}),
    )


@pytest.fixture(scope="session")
def live():
    if os.environ.get("PHASE4_TEST") != "1":
        raise RuntimeError("Explicitly start Phase 4 fixtures and set PHASE4_TEST=1")
    owned = json.loads((ROOT / ".artifacts/phase4/test-databases.json").read_text())
    assert {database for _, database, _ in CLONES} <= set(owned)
    urls = {
        "post": {
            "node": published("post-reference", 3003),
            "python": published("post-candidate", 3003),
        },
        "dependencies": {
            kind: published(f"dependencies-{kind}", 3010) for kind in ("node", "python")
        },
        "search": {kind: published(f"search-phase4-{kind}", 3008) for kind in ("node", "python")},
        "favorite": published("favorite-phase4", 3009),
        "gateway": published("gateway-phase4", 3000),
    }
    with httpx.Client(timeout=30, trust_env=False) as client:
        for url in urls["post"].values():
            deadline = time.monotonic() + 30
            while True:
                try:
                    if client.get(url + "/unknown/probe").status_code == 404:
                        break
                except httpx.HTTPError:
                    pass
                if time.monotonic() > deadline:
                    raise RuntimeError("Post fixture not ready")
                time.sleep(0.2)
        yield client, urls


def events(live, kind, dependency=None):
    client, urls = live
    data = client.get(urls["dependencies"][kind] + "/__events").json()
    return [
        event for event in data["events"] if dependency is None or event["dependency"] == dependency
    ]


def wait_for(check):
    deadline = time.monotonic() + 8
    while True:
        result = check()
        if result:
            return result
        if time.monotonic() >= deadline:
            raise AssertionError("Asynchronous dependency did not produce expected result")
        time.sleep(0.1)


def file_inventory(kind):
    service = "post-reference" if kind == "node" else "post-candidate"
    if kind == "node":
        script = (
            "const fs=require('fs');"
            "process.stdout.write(JSON.stringify(fs.readdirSync('/app/uploads')));"
        )
        return set(json.loads(docker("exec", container(service), "node", "-e", script)))
    script = "import os,json; print(json.dumps(os.listdir('/app/uploads')))"
    return set(json.loads(docker("exec", container(service), "python", "-c", script)))


def remove_owned_files(kind, names):
    assert all(re.fullmatch(r"\d+-phase4_test_[^/\\]+", name) for name in names)
    service = "post-reference" if kind == "node" else "post-candidate"
    if kind == "node":
        script = (
            "const fs=require('fs');for(const n of JSON.parse(fs.readFileSync(0,'utf8')))"
            "fs.unlinkSync('/app/uploads/'+n);"
        )
        docker(
            "exec",
            "-i",
            container(service),
            "node",
            "-e",
            script,
            input_data=json.dumps(sorted(names)),
        )
    else:
        script = (
            "import sys,json,pathlib; "
            "[(pathlib.Path('/app/uploads') / n).unlink() for n in json.load(sys.stdin)]"
        )
        docker(
            "exec",
            "-i",
            container(service),
            "python",
            "-c",
            script,
            input_data=json.dumps(sorted(names)),
        )


@pytest.fixture(autouse=True)
def owned_cleanup(live):
    client, urls = live
    before = {kind: file_inventory(kind) for kind in ("node", "python")}

    def clean():
        # Drain observed dependency work before removing owned fixture rows.
        time.sleep(0.2)
        for url in urls["dependencies"].values():
            wait_for(lambda url=url: client.get(url + "/__events").json()["pending"] == 0)
            assert client.post(url + "/__control", json={}).status_code == 200
        queries = {}
        for kind, database, tables in CLONES:
            queries.setdefault(kind, []).extend(
                f"DELETE FROM `{database}`.`{table}`" for table in reversed(tables)
            )
        for kind, statements in queries.items():
            select(kind, ";".join(statements))

    clean()
    try:
        yield
    finally:
        clean()
        for kind, original in before.items():
            current = file_inventory(kind)
            assert original <= current, "Pre-existing fixture file lost"
            remove_owned_files(kind, current - original)
            assert file_inventory(kind) == original


def compare_record(node, python, generated=False):
    assert set(node) == set(python)
    for key, value in node.items():
        if key in {"createdAt", "updatedAt"}:
            assert value.endswith("Z") and python[key].endswith("Z")
            assert len(value.split(".")[1]) == len(python[key].split(".")[1]) == 4
            assert abs(
                (
                    datetime.fromisoformat(value) - datetime.fromisoformat(python[key])
                ).total_seconds()
            ) < (5 if generated else 0.001)
        elif key == "id" and generated:
            assert isinstance(value, int) and isinstance(python[key], int)
        elif key == "Images":
            assert len(value) == len(python[key])
            for left, right in zip(value, python[key], strict=True):
                compare_record(left, right, generated)
        else:
            assert value == python[key]


def seed_posts():
    for database in POST_DBS.values():
        select(
            "post",
            f"INSERT INTO `{database}`.posts "
            "(id,userId,categoryId,title,description,price,status,`condition`,createdAt,updatedAt) "
            "VALUES "
            f"(4,{USER_ID},1,'phase4_test Alpha','',12.50,'available','custom',"
            "'2026-01-02','2026-01-02'),"
            f"(5,{USER_ID + 1},2,'phase4_test beta',NULL,0,'approved',NULL,"
            "'2026-01-03','2026-01-03'),"
            f"(6,{USER_ID},999999,'phase4_test pending',NULL,1.99,'pending',NULL,"
            "'2026-01-04','2026-01-04');"
            f"INSERT INTO `{database}`.images (id,postId,imageUrl,createdAt,updatedAt) VALUES "
            "(1,4,'/uploads/phase4_test_fixture.bin','2026-01-02','2026-01-02'),"
            "(2,4,'/uploads/phase4_test_fixture2.bin','2026-01-02','2026-01-02')",
        )


def headers(**kwargs):
    return {"Authorization": "Bearer " + signed_token(**kwargs), "X-Request-ID": "phase4-test"}
