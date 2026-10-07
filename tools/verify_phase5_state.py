"""Phase 5 repository/runtime preservation and full-row content hashes."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import httpx
from verify_runtime import command, select, snapshot

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / ".artifacts/phase5"
ALLOWED = {
    f"{service}/{name}"
    for service in ("favorite-service", "review-service", "search-service")
    for name in (
        ".env.example",
        "common/logging.py",
        "config/settings.py",
        "config/urls.py",
        "requirements.txt",
        "requirements.lock.txt",
        "tests/test_health.py",
    )
} | {"review-service/config/wsgi.py", "tools/verify_phase4_uploads.py"}


def content_snapshot():
    schemas = json.loads((ARTIFACTS / "db-before.json").read_text(encoding="utf-8-sig"))
    result = {}
    for database, info in schemas.items():
        kind = database.removesuffix("_db")
        for table in info["tables"]:
            columns = select(
                kind,
                "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                f"WHERE TABLE_SCHEMA='{database}' AND TABLE_NAME='{table}' "
                "ORDER BY ORDINAL_POSITION",
            ).splitlines()
            assert all(re.fullmatch(r"[A-Za-z0-9_]+", name) for name in columns)
            expression = ",".join(f"`{column}`" for column in columns)
            rows = select(
                kind,
                f"SET NAMES utf8mb4; SELECT JSON_ARRAY({expression}) FROM `{database}`.`{table}`",
            ).splitlines()
            digest = hashlib.sha256("\n".join(sorted(rows)).encode()).hexdigest()
            result[f"{database}.{table}"] = {"count": len(rows), "contentSha256": digest}
    return result


def search_http():
    before = json.loads((ARTIFACTS / "search-http-before.json").read_text())
    with httpx.Client(timeout=40, trust_env=False) as client:
        for item in before:
            response = client.get("http://127.0.0.1:3000/search", params=item["params"])
            assert response.status_code == 200
            data = response.json()
            encoded = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            assert len(data) == item["count"]
            assert hashlib.sha256(encoded.encode()).hexdigest() == item["sha256"]
    print("PASS: canonical Django Search HTTP responses equal pre-cutover Node baseline")


def files():
    before = json.loads((ARTIFACTS / "before-filehashes.json").read_text(encoding="utf-8-sig"))
    modified = []
    for name, digest in before.items():
        path = ROOT / name
        assert path.is_file(), "Pre-existing repository file missing"
        if hashlib.sha256(path.read_bytes()).hexdigest().upper() != digest.upper():
            modified.append(name)
    assert set(modified) <= ALLOWED, "Unexpected edit outside Phase 5 scope"
    names = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    ).splitlines()
    assert not subprocess.check_output(
        ["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True
    ).strip()
    result = {
        "baselineFiles": len(before),
        "preserved": len(before) - len(modified),
        "created": sorted(set(names) - set(before)),
        "modified": sorted(modified),
    }
    (ARTIFACTS / "file-changes.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    sections = [
        "# Phase 5 file manifest\n",
        f"Baseline: {len(before)} files; {result['preserved']} unchanged; "
        f"{len(modified)} modified; {len(result['created'])} created.\n",
    ]
    for label in ("created", "modified"):
        sections += [f"## {label.title()}\n", "```text\n" + "\n".join(result[label]) + "\n```\n"]
    (ROOT / "docs/migration/phase-5-files.md").write_text("\n".join(sections), encoding="utf-8")
    print(
        f"PASS: {result['preserved']} baseline files unchanged; "
        f"{len(modified)} permitted edits; {len(result['created'])} new files"
    )


def runtime():
    before = json.loads((ARTIFACTS / "preserved-runtime.json").read_text(encoding="utf-8-sig"))
    for service, expected in before.items():
        current = command(
            ["docker", "inspect", service, "--format", "{{.Id}} {{.Image}} {{.State.StartedAt}}"]
        ).strip()
        if service == "post-service":
            assert current.split()[1] == expected.split()[1], "Post image changed"
        else:
            assert current == expected, "Preserved container identity/image/start changed"
    containers = json.loads(
        command(
            [
                "docker",
                "inspect",
                "review-service",
                "search-service",
                "favorite-service",
                "post-service",
                "auth-service",
            ]
        )
    )
    review, search, favorite, post, auth = containers
    envs = [
        dict(item.split("=", 1) for item in row["Config"]["Env"] if "=" in item)
        for row in containers
    ]
    for row, env, kind, port in zip(
        containers[:3], envs[:3], ("review", "search", "favorite"), (3007, 3008, 3009), strict=True
    ):
        assert row["Config"]["Image"] == f"kientrucpm-{kind}-python-phase5"
        assert row["State"]["Health"]["Status"] == "healthy"
        assert any("gunicorn" in part for part in row["Config"]["Cmd"])
        assert env["DB_NAME"] == kind + "_db" and env["PORT"] == str(port)
        assert not env.get("NODE_OPTIONS")
    assert envs[2]["JWT_SECRET"] == envs[4]["JWT_SECRET"]
    assert envs[2]["POST_SERVICE_URL"] == "http://post-service:3003"
    assert envs[0]["POST_SERVICE_URL"] == "http://post-service:3003"
    assert envs[3]["SEARCH_SERVICE_URL"] == "http://search-service:3008"
    assert envs[3]["MESSAGE_SERVICE_URL"] == "http://message-service:3005"
    for row in (post, review):
        mounts = [mount for mount in row["Mounts"] if mount["Destination"] == "/app/uploads"]
        assert len(mounts) == 1 and mounts[0]["Type"] == "volume" and mounts[0]["RW"]
        assert mounts[0]["Name"] == "kientrucpm_shared_uploads"
    for service, port in [
        ("api-gateway", 3000),
        ("auth-service", 3001),
        ("user-service", 3002),
        ("post-service", 3003),
        ("category-service", 3004),
        ("review-service", 3007),
        ("search-service", 3008),
        ("favorite-service", 3009),
    ]:
        script = (
            "import urllib.request,json;\nfor path in ['/health','/ready']:\n"
            + f" with urllib.request.urlopen('http://127.0.0.1:{port}'+path,"
            + "timeout=10) as response:\n"
            + "  assert response.status==200\n"
        )
        command(["docker", "exec", service, "python", "-c", script])
    print(
        "PASS: eight canonical Python services healthy/ready; original uploads/JWT/DNS; "
        "preserved Node/frontend runtimes"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-content", action="store_true")
    parser.add_argument("--compare-content", action="store_true")
    parser.add_argument("--files", action="store_true")
    parser.add_argument("--runtime", action="store_true")
    parser.add_argument("--search-http", action="store_true")
    args = parser.parse_args()
    if args.snapshot_content:
        (ARTIFACTS / "db-content-before.json").write_text(
            json.dumps(content_snapshot(), indent=2) + "\n", encoding="utf-8"
        )
        print("Recorded content hashes of every legacy table; contents withheld")
    if args.compare_content:
        assert content_snapshot() == json.loads(
            (ARTIFACTS / "db-content-before.json").read_text()
        ), "Pre-existing business row content changed"
        assert snapshot() == json.loads(
            (ARTIFACTS / "db-before.json").read_text(encoding="utf-8-sig")
        )
        print(
            "PASS: all eight DB schemas/counts and complete legacy table content hashes unchanged"
        )
    if args.files:
        files()
    if args.runtime:
        runtime()
    if args.search_http:
        search_http()


if __name__ == "__main__":
    main()
