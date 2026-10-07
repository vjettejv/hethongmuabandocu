import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from verify_runtime import select  # noqa: E402

DATABASES = {"node": "phase2_auth_node", "python": "phase2_auth_python"}


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
    if not identifier or "\n" in identifier:
        raise RuntimeError(f"Expected one test container: {service}")
    return identifier


def published_url(service, port):
    data = json.loads(docker("inspect", container(service)))[0]
    mapping = data["NetworkSettings"]["Ports"][f"{port}/tcp"][0]
    assert mapping["HostIp"] == "127.0.0.1"
    return "http://127.0.0.1:" + mapping["HostPort"]


def sql_literal(value):
    return "CONVERT(0x" + value.encode("utf-8").hex() + " USING utf8mb4)"


def rows(kind):
    name = DATABASES[kind]
    value = select(
        "auth",
        f"SELECT COALESCE(JSON_ARRAYAGG(JSON_OBJECT("
        f"'id',id,'username',username,'email',email,'password',password,'roleId',roleId,"
        f"'verified',isVerified,'otp',otp)), JSON_ARRAY()) FROM `{name}`.users",
    )
    return json.loads(value)


NODE_CRYPTO = """
const fs = require('fs'), jwt = require('jsonwebtoken'), bcrypt = require('bcryptjs');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
(async () => {
 let result;
 if (input.action === 'sign') result = jwt.sign(input.claims, process.env.JWT_SECRET,
     input.expired ? {expiresIn:-10} : {expiresIn:'1d'});
 if (input.action === 'verify') result = jwt.verify(input.token, process.env.JWT_SECRET);
 if (input.action === 'hash') result = await bcrypt.hash(input.password,10);
 if (input.action === 'compare') result = await bcrypt.compare(input.password,input.hash);
 process.stdout.write(JSON.stringify(result));
})().catch(() => process.exit(1));
"""


def node_crypto(**arguments):
    return json.loads(
        docker(
            "exec",
            "-i",
            container("auth-reference"),
            "node",
            "-e",
            NODE_CRYPTO,
            input_data=json.dumps(arguments),
        )
    )


@pytest.fixture(scope="session")
def live():
    if os.environ.get("PHASE2_TEST") != "1":
        raise RuntimeError("Set PHASE2_TEST=1 and explicitly start isolated Phase 2 test services")
    owned = json.loads((ROOT / ".artifacts/phase2/test-databases.json").read_text())
    assert set(DATABASES.values()) | {"phase2_user_test"} <= set(owned)
    urls = {
        "node": published_url("auth-reference", 3001),
        "python": published_url("auth-candidate", 3001),
    }
    with httpx.Client(timeout=12, trust_env=False) as client:
        for url in urls.values():
            deadline = time.monotonic() + 30
            while True:
                try:
                    response = client.get(url + "/missing-probe")
                    if response.status_code == 404:
                        break
                except httpx.HTTPError:
                    pass
                if time.monotonic() >= deadline:
                    raise RuntimeError("Auth test service did not become ready")
                time.sleep(0.25)
        yield client, urls


@pytest.fixture(autouse=True)
def clean_owned_clones(live):
    for name in DATABASES.values():
        select("auth", f"DELETE FROM `{name}`.users")
    select("user", "DELETE FROM phase2_user_test.userprofiles")
    yield
    for name in DATABASES.values():
        select("auth", f"DELETE FROM `{name}`.users")
    select("user", "DELETE FROM phase2_user_test.userprofiles")


def seed(encoded, *, verified=True):
    for name in DATABASES.values():
        select(
            "auth",
            f"INSERT INTO `{name}`.users "
            "(username,email,password,roleId,isVerified,otp,createdAt,updatedAt) VALUES ("
            f"'fixture','fixture@example.invalid',{sql_literal(encoded)},2,{int(verified)},"
            "'654321',UTC_TIMESTAMP(),UTC_TIMESTAMP())",
        )


def request_pair(live, method, path, payload=None, headers=None):
    client, urls = live
    return {
        kind: client.request(method, url + path, json=payload, headers=headers)
        for kind, url in urls.items()
    }


def compare(pair, status):
    node, python = pair["node"], pair["python"]
    assert node.status_code == python.status_code == status
    assert (
        node.headers["content-type"].split(";")[0] == python.headers["content-type"].split(";")[0]
    )

    def shape(value):
        if isinstance(value, dict):
            return {key: shape(item) for key, item in value.items()}
        return type(value).__name__

    assert shape(node.json()) == shape(python.json())
