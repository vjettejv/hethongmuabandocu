"""Phase 6 preservation checks. No migration, table repair or baseline overwrite."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import verify_phase5_state
from verify_phase4_uploads import inventory
from verify_runtime import command, snapshot

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / ".artifacts/phase6"
ALLOWED = {
    f"{service}/{name}"
    for service in ("message-service", "notification-service")
    for name in (
        ".env.example",
        "common/logging.py",
        "config/settings.py",
        "config/urls.py",
        "requirements.txt",
        "requirements.lock.txt",
        "tests/test_health.py",
    )
} | {
    "message-service/config/asgi.py",
    "message-service/Dockerfile.python",
    "requirements-dev.txt",
    "requirements-dev.lock.txt",
}
PORTS = {
    "api-gateway": 3000,
    "auth-service": 3001,
    "user-service": 3002,
    "post-service": 3003,
    "category-service": 3004,
    "message-service": 3005,
    "notification-service": 3006,
    "review-service": 3007,
    "search-service": 3008,
    "favorite-service": 3009,
}


def preservation():
    verify_phase5_state.ARTIFACTS = ARTIFACTS
    assert verify_phase5_state.content_snapshot() == json.loads(
        (ARTIFACTS / "db-content-before.json").read_text()
    )
    assert snapshot() == json.loads((ARTIFACTS / "db-before.json").read_text(encoding="utf-8-sig"))
    assert inventory() == json.loads((ARTIFACTS / "uploads-before.json").read_text())
    print("PASS: eight legacy schemas/counts/full-row hashes and all 46 uploads unchanged")


def files():
    before = json.loads((ARTIFACTS / "before-filehashes.json").read_text(encoding="utf-8-sig"))
    modified = []
    for name, digest in before.items():
        path = ROOT / name
        assert path.is_file(), "Pre-existing repository file missing"
        if hashlib.sha256(path.read_bytes()).hexdigest().lower() != digest.lower():
            modified.append(name)
    assert set(modified) <= ALLOWED, "Unexpected edit outside Phase 6 scope"
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
        "modified": sorted(modified),
        "created": sorted(set(names) - set(before)),
    }
    (ARTIFACTS / "file-changes.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    content = [
        "# Phase 6 file manifest",
        f"Baseline {len(before)} files; {result['preserved']} unchanged; "
        f"{len(modified)} modified; {len(result['created'])} created.",
    ]
    for key in ("created", "modified"):
        content.extend([f"## {key.title()}", "```text\n" + "\n".join(result[key]) + "\n```"])
    (ROOT / "docs/migration/phase-6-files.md").write_text(
        "\n\n".join(content) + "\n", encoding="utf-8"
    )
    print(
        f"PASS: {result['preserved']} baseline files unchanged; "
        f"{len(modified)} permitted edits; {len(result['created'])} new files; staging empty"
    )


def runtime():
    before = json.loads((ARTIFACTS / "runtime-before.json").read_text())
    after = {}
    for service, expected in before.items():
        current = command(
            ["docker", "inspect", service, "--format", "{{.Id}} {{.Image}} {{.State.StartedAt}}"]
        ).strip()
        after[service] = current
        if service in {"message-service", "notification-service"}:
            assert current.split()[1] != expected.split()[1]
        elif service == "search-service":
            assert current.split()[1] == expected.split()[1], "Preserved Search image changed"
        else:
            assert current == expected, "Preserved container identity/image/start changed"
    rows = json.loads(command(["docker", "inspect", *PORTS]))
    envs = {
        row["Name"].lstrip("/"): dict(
            item.split("=", 1) for item in row["Config"]["Env"] if "=" in item
        )
        for row in rows
    }
    for row in rows:
        service = row["Name"].lstrip("/")
        assert row["State"]["Health"]["Status"] == "healthy"
        assert not envs[service].get("NODE_OPTIONS")
        script = (
            "import urllib.request;\nfor path in ['/health','/ready']:\n"
            f" with urllib.request.urlopen('http://127.0.0.1:{PORTS[service]}'+path,"
            "timeout=10) as response:\n"
            "  assert response.status==200\n"
        )
        command(["docker", "exec", service, "python", "-c", script])
    message = next(row for row in rows if row["Name"] == "/message-service")
    notification = next(row for row in rows if row["Name"] == "/notification-service")
    assert message["Config"]["Image"] == "kientrucpm-message-python-phase6"
    assert notification["Config"]["Image"] == "kientrucpm-notification-python-phase6"
    assert "--workers 1" in " ".join(message["Config"]["Cmd"])
    assert envs["message-service"]["DB_NAME"] == "message_db"
    assert envs["search-service"]["DB_NAME"] == "search_db"
    assert envs["message-service"]["JWT_SECRET"] == envs["auth-service"]["JWT_SECRET"]
    for dependency, port in [("USER", 3002), ("AUTH", 3001), ("NOTIFICATION", 3006)]:
        assert (
            envs["message-service"][dependency + "_SERVICE_URL"]
            == f"http://{dependency.lower()}-service:{port}"
        )
    assert envs["post-service"]["MESSAGE_SERVICE_URL"] == "http://message-service:3005"
    for service in ("post-service", "review-service"):
        row = next(row for row in rows if row["Name"] == "/" + service)
        mounts = [mount for mount in row["Mounts"] if mount["Destination"] == "/app/uploads"]
        assert (
            len(mounts) == 1
            and mounts[0]["Name"] == "kientrucpm_shared_uploads"
            and mounts[0]["RW"]
        )
    (ARTIFACTS / "runtime-after.json").write_text(
        json.dumps(after, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "PASS: ten canonical Python services healthy/ready; one Message ASGI worker; "
        "shared JWT/DNS; original Post/Review uploads"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preservation", action="store_true")
    parser.add_argument("--files", action="store_true")
    parser.add_argument("--runtime", action="store_true")
    args = parser.parse_args()
    if args.preservation:
        preservation()
    if args.files:
        files()
    if args.runtime:
        runtime()


if __name__ == "__main__":
    main()
