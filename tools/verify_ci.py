"""Portable, disposable all-Python integration runner derived from canonical Compose.

Never mounts canonical volumes, reads the developer .env or imports seed user rows.
Use --validate-only for Compose validation; --smoke selects the PR integration gate.
"""

import argparse
import json
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import yaml
from verify_runtime import SERVICES

ROOT = Path(__file__).resolve().parents[1]


def synthetic_schema(kind):
    text = (ROOT / "seeds/schema" / f"{kind}.sql").read_text(encoding="utf-8-sig")
    statements = re.findall(r"CREATE TABLE `\w+` \(.*?\) ENGINE=.*?;", text, re.S)
    if not statements:
        raise RuntimeError(f"Missing schema template: {kind}")
    ddl = (
        "SET FOREIGN_KEY_CHECKS=0;\n"
        + "\n".join(
            re.sub(r"AUTO_INCREMENT=\d+", "AUTO_INCREMENT=1", value) for value in statements
        )
        + "\nSET FOREIGN_KEY_CHECKS=1;\n"
    )
    if kind == "category":
        ddl += "INSERT INTO categories VALUES (1,'CI category',NULL,'2026-01-01','2026-01-01');\n"
    elif kind == "user":
        ddl += "ALTER TABLE userprofiles AUTO_INCREMENT=1001;\n"
    elif kind == "search":
        ddl += (
            "CREATE DATABASE phase7_search_e2e;"
            "CREATE TABLE phase7_search_e2e.searchindices LIKE search_db.searchindices;\n"
        )
    return ddl


def configuration(project, folder):
    if not re.fullmatch(r"marketplace-ci-[0-9a-f]{12}", project):
        raise ValueError("CI project must have an owned UUID name")
    config = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    config["name"] = project
    config.pop("x-node-guard", None)
    config["networks"]["do-cu-micro-net"]["name"] = project + "-network"
    for name, volume in config["volumes"].items():
        volume["name"] = project + "-" + name
        volume.pop("external", None)
    for name, service in config["services"].items():
        service["container_name"] = project + "-" + service["container_name"]
        service["restart"] = "no"
        service.pop("ports", None)
        if "build" in service:
            service["build"]["context"] = str((ROOT / service["build"]["context"]).resolve())
            service["image"] = project + "-" + name
        if name.endswith("-db"):
            # Eight fresh MySQL instances must fit on a standard CI runner.
            # These resource settings apply only to disposable test databases.
            service["command"] += [
                "--innodb-redo-log-capacity=16777216",
                "--innodb-buffer-pool-size=33554432",
                "--max-connections=50",
            ]
            kind = name.removesuffix("-db")
            path = folder / f"{kind}.sql"
            path.write_text(synthetic_schema(kind), encoding="utf-8")
            service["volumes"] = [
                {"type": "volume", "source": kind + "_data", "target": "/var/lib/mysql"},
                {
                    "type": "bind",
                    "source": str(path),
                    "target": "/docker-entrypoint-initdb.d/1_ci.sql",
                    "read_only": True,
                },
            ]
        if name == "frontend":
            service["ports"] = [{"target": 80, "published": "0", "host_ip": "127.0.0.1"}]
        if name == "search-service":
            service["environment"]["DB_NAME"] = "phase7_search_e2e"
    return config


def assert_isolated(config, project):
    assert len(config["services"]) == 19
    assert set(SERVICES) <= set(config["services"])
    for service in config["services"].values():
        assert service["container_name"].startswith(project + "-")
        for mount in service.get("volumes", []):
            if mount["type"] == "volume":
                assert mount["source"] in config["volumes"]
    for volume in config["volumes"].values():
        assert volume["name"].startswith(project + "-") and not volume.get("external")
    assert all("kientrucpm_" not in value["name"] for value in config["volumes"].values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    project = "marketplace-ci-" + uuid4().hex[:12]
    folder = ROOT / ".artifacts/ci" / project
    folder.mkdir(parents=True)
    config = configuration(project, folder)
    assert_isolated(config, project)
    compose_path = folder / "compose.yml"
    compose_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    environment = os.environ.copy()
    environment.update(
        MYSQL_ROOT_PASSWORD=secrets.token_hex(24),
        PYTHON_DB_USER="root",
        PYTHON_SECRET_KEY=secrets.token_hex(48),
        JWT_SECRET=secrets.token_hex(48),
        NODE_ENV="development",
        MOCK_EMAIL="true",
        SMTP_HOST="smtp.example.invalid",
        SMTP_PORT="587",
        SMTP_USER="",
        SMTP_PASS="",
    )
    environment["PYTHON_DB_PASSWORD"] = environment["MYSQL_ROOT_PASSWORD"]
    env_path = folder / "test.env"
    keys = (
        "MYSQL_ROOT_PASSWORD",
        "PYTHON_DB_USER",
        "PYTHON_DB_PASSWORD",
        "PYTHON_SECRET_KEY",
        "JWT_SECRET",
        "NODE_ENV",
        "MOCK_EMAIL",
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USER",
        "SMTP_PASS",
    )
    env_path.write_text("\n".join(f"{key}={environment[key]}" for key in keys), encoding="utf-8")
    base = ["docker", "compose", "--env-file", str(env_path), "-p", project]

    def compose(*arguments, canonical=False):
        path = ROOT / "docker-compose.yml" if canonical else compose_path
        command = [*base, "-f", str(path), *arguments]
        with (folder / "compose.log").open("a", encoding="utf-8") as log:
            result = subprocess.run(
                command,
                cwd=ROOT,
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=600,
            )
        if result.returncode:
            raise RuntimeError(
                f"Compose {arguments[0]} failed; inspect ignored {folder / 'compose.log'}"
            )

    try:
        compose("config", "--quiet", canonical=True)
        compose("config", "--quiet")
    except BaseException:
        env_path.unlink(missing_ok=True)
        raise
    print("PASS: canonical Compose and isolated 19-container configuration", flush=True)
    if args.validate_only:
        env_path.unlink()
        return
    try:
        compose("up", "-d", "--build", "--wait", "--wait-timeout", "240")
        output = subprocess.check_output(
            [*base, "-f", str(compose_path), "port", "frontend", "80"],
            cwd=ROOT,
            env=environment,
            text=True,
            encoding="utf-8",
            timeout=60,
        ).strip()
        if not re.fullmatch(r"127\.0\.0\.1:\d+", output):
            raise RuntimeError("Unexpected isolated frontend binding")
        evidence = folder / "phase7"
        evidence.mkdir()
        environment.update(
            PHASE7_TEST="1",
            CANONICAL_TEST_PREFIX=project + "-",
            CANONICAL_TEST_BASE_URL="http://" + output,
            CANONICAL_TEST_ARTIFACTS=str(evidence),
        )
        probe = subprocess.run(
            [
                "docker",
                "exec",
                project + "-do-cu-search-db",
                "sh",
                "-c",
                'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -h127.0.0.1 -uroot -e '
                '"SELECT COUNT(*) FROM phase7_search_e2e.searchindices"',
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            check=False,
        )
        if probe.returncode:
            code = re.search(r"ERROR (\d+)", probe.stderr)
            raise RuntimeError(
                "Isolated Search schema probe failed; MySQL code "
                + (code.group(1) if code else "unavailable")
            )
        command = [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            "integration-tests/phase7/pytest.ini",
            "integration-tests/phase7",
            "-q",
            f"--junitxml={folder / 'integration.xml'}",
        ]
        if args.smoke:
            command += ["-k", "test_full_business_lifecycle or test_health_ready_openapi"]
        result = subprocess.run(command, cwd=ROOT, env=environment, check=False)
        if result.returncode:
            raise RuntimeError("Canonical Python integration failed")
        (folder / "result.json").write_text(
            json.dumps(
                {
                    "project": project,
                    "status": "PASS",
                    "suite": "smoke" if args.smoke else "full",
                    "backend": "Python only",
                }
            ),
            encoding="utf-8",
        )
    finally:
        # Only this UUID's managed volumes are removed, never canonical external volumes.
        assert_isolated(config, project)
        try:
            compose("down", "--volumes")
        finally:
            env_path.unlink(missing_ok=True)
        print("Cleaned UUID-owned CI containers/network/volumes", flush=True)


if __name__ == "__main__":
    main()
