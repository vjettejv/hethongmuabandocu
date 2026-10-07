import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from prepare_phase3_tests import CLONES  # noqa: E402
from verify_runtime import select  # noqa: E402

AUTH_ID = 3100100
USER_DBS = {"node": "phase3_user_node", "python": "phase3_user_python"}
CATEGORY_DBS = {"node": "phase3_category_node", "python": "phase3_category_python"}


def docker(*arguments, input_data=None):
    result = subprocess.run(
        ["docker", *arguments],
        input=input_data,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Docker test operation failed (exit {result.returncode})")
    return result.stdout.strip()


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
        raise RuntimeError(f"Expected one test container: {service}")
    return value


def published_url(service, port):
    data = json.loads(docker("inspect", container(service)))[0]
    mapping = data["NetworkSettings"]["Ports"][f"{port}/tcp"][0]
    assert mapping["HostIp"] == "127.0.0.1"
    return "http://127.0.0.1:" + mapping["HostPort"]


def literal(value):
    return "CONVERT(0x" + value.encode("utf-8").hex() + " USING utf8mb4)"


def node_token(auth_id=AUTH_ID, *, expired=False):
    script = """
const fs=require('fs'), jwt=require('jsonwebtoken');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(jwt.sign({id:input.id,roleId:1},process.env.JWT_SECRET,
                             {expiresIn:input.expired?-10:'1d'}));
"""
    return docker(
        "exec",
        "-i",
        container("user-reference"),
        "node",
        "-e",
        script,
        input_data=json.dumps({"id": auth_id, "expired": expired}),
    )


@pytest.fixture(scope="session")
def live():
    if os.environ.get("PHASE3_TEST") != "1":
        raise RuntimeError("Set PHASE3_TEST=1 and start isolated Phase 3 services explicitly")
    owned = json.loads((ROOT / ".artifacts/phase3/test-databases.json").read_text())
    assert {database for _, database, _ in CLONES} <= set(owned)
    urls = {
        "user": {
            "node": published_url("user-reference", 3002),
            "python": published_url("user-candidate", 3002),
        },
        "category": {
            "node": published_url("category-reference", 3004),
            "python": published_url("category-candidate", 3004),
        },
        "gateway": published_url("gateway-phase3-probe", 3000),
        "message": published_url("message-cross", 3005),
        "post": published_url("post-cross", 3003),
        "search_fixture": published_url("phase3-search-fixture", 3008),
    }
    with httpx.Client(timeout=20, trust_env=False) as client:
        for url in [*urls["user"].values(), *urls["category"].values()]:
            deadline = time.monotonic() + 30
            while True:
                try:
                    if client.get(url + "/unknown/probe").status_code == 404:
                        break
                except httpx.HTTPError:
                    pass
                if time.monotonic() >= deadline:
                    raise RuntimeError("Phase 3 test service did not become ready")
                time.sleep(0.25)
        yield client, urls


@pytest.fixture(autouse=True)
def clean_owned_schemas(live):
    def clean():
        queries = {}
        for kind, database, tables in CLONES:
            queries.setdefault(kind, []).extend(
                f"DELETE FROM `{database}`.`{table}`" for table in reversed(tables)
            )
        for kind, statements in queries.items():
            select(kind, ";".join(statements))

    clean()
    yield
    clean()


def pair(live, service, method, path, *, payload=None, headers=None):
    client, urls = live
    return {
        kind: client.request(method, url + path, json=payload, headers=headers)
        for kind, url in urls[service].items()
    }


def compare(pair, status):
    node, python = pair["node"], pair["python"]
    assert node.status_code == python.status_code == status
    assert (
        node.headers["content-type"].split(";")[0] == python.headers["content-type"].split(";")[0]
    )


def compare_records(node, python, *, generated=False):
    assert set(node) == set(python)
    for key in node:
        if key in {"createdAt", "updatedAt"}:
            left, right = datetime.fromisoformat(node[key]), datetime.fromisoformat(python[key])
            assert node[key].endswith("Z") and python[key].endswith("Z")
            assert len(node[key].split(".")[1]) == len(python[key].split(".")[1]) == 4
            assert abs((left - right).total_seconds()) < (3 if generated else 0.001)
        elif generated and key == "id":
            assert isinstance(node[key], int) and isinstance(python[key], int)
        else:
            assert node[key] == python[key]


def seed_profiles():
    for database in USER_DBS.values():
        select(
            "user",
            f"INSERT INTO `{database}`.userprofiles "
            "(id,authId,fullName,phone,address,avatar,createdAt,updatedAt) VALUES "
            f"(4,{AUTH_ID},'phase3_test_name','phone','address',NULL,"
            "'2026-01-02 00:00:00','2026-01-02 00:00:00')",
        )


def profile_rows(kind):
    return json.loads(
        select(
            "user",
            "SET NAMES utf8mb4; SELECT COALESCE(JSON_ARRAYAGG(JSON_OBJECT("
            "'id',id,'authId',authId,'fullName',fullName,'phone',phone,'address',address,"
            f"'avatar',avatar)),JSON_ARRAY()) FROM `{USER_DBS[kind]}`.userprofiles",
        )
    )
