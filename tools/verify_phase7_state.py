"""Phase 7 safety gates reuse the established database and upload readers."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import verify_phase5_state
from verify_phase4_uploads import inventory
from verify_runtime import SERVICES, command, snapshot

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / ".artifacts/phase7"


def save(name, value):
    (ARTIFACTS / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def preservation():
    verify_phase5_state.ARTIFACTS = ARTIFACTS
    for name, current in (
        ("db-before.json", snapshot()),
        ("db-content-before.json", verify_phase5_state.content_snapshot()),
        ("uploads-before.json", inventory()),
    ):
        assert current == json.loads((ARTIFACTS / name).read_text()), name + " changed"
    print("PASS: eight database schemas/counts/full-row hashes and all upload bytes unchanged")


def files():
    before = json.loads((ARTIFACTS / "before-filehashes.json").read_text())
    names = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    ).splitlines()
    removed, modified = [], []
    for name, expected in before.items():
        path = ROOT / name
        if not path.is_file():
            removed.append(name)
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            modified.append(name)
    assert "HUONG_DAN_TRIEN_KHAI.md" not in removed + modified
    assert ".gitignore" not in removed + modified
    assert not command(["git", "diff", "--cached", "--name-only"]).strip()
    retirement = ARTIFACTS / "retirement.json"
    allowed = json.loads(retirement.read_text()) if retirement.exists() else []
    assert set(removed) <= {row["path"] for row in allowed}, "Unmanifested removal"
    assert not any(name.endswith(".py") for name in removed), "Python file removed"
    frontend = {name for name in before if name.startswith("do-cu-frontend/")}
    assert not frontend.intersection(removed + modified), "Frontend changed"
    result = {
        "baselineFiles": len(before),
        "preserved": len(before) - len(removed) - len(modified),
        "removed": sorted(removed),
        "modified": sorted(modified),
        "created": sorted(name for name in set(names) - set(before) if (ROOT / name).is_file()),
    }
    save("file-changes.json", result)
    print("PASS: protected guide/frontend/gitignore byte-identical, index empty, manifest removals")


def runtime():
    results = []
    environments = {}
    for name, port in SERVICES.items():
        row = json.loads(command(["docker", "inspect", name]))[0]
        assert row["State"]["Health"]["Status"] == "healthy", name
        assert "python" in row["Config"]["Image"] or name in {"api-gateway", "auth-service"}
        assert "node" not in " ".join(row["Config"]["Cmd"])
        script = (
            "import urllib.request;\nfor path in ['/health','/ready']:\n"
            f" assert urllib.request.urlopen('http://127.0.0.1:{port}'+path,timeout=8).status==200"
        )
        command(["docker", "exec", name, "python", "-c", script])
        env = dict(item.split("=", 1) for item in row["Config"]["Env"] if "=" in item)
        environments[name] = env
        if name not in {"api-gateway", "notification-service"}:
            assert env["DB_NAME"] == name.removesuffix("-service") + "_db"
        if name == "message-service":
            assert "--workers 1" in " ".join(row["Config"]["Cmd"])
        if name in {"post-service", "review-service"}:
            assert [m["Name"] for m in row["Mounts"] if m["Destination"] == "/app/uploads"] == [
                "kientrucpm_shared_uploads"
            ]
        results.append({"service": name, "runtime": "Python", "port": port, "health": "ready"})
    for name, port in SERVICES.items():
        if name == "api-gateway":
            continue
        key = name.removesuffix("-service").upper() + "_SERVICE_URL"
        assert environments["api-gateway"][key] == f"http://{name}:{port}"
    for name in ("user-service", "post-service", "message-service", "favorite-service"):
        assert environments[name]["JWT_SECRET"] == environments["auth-service"]["JWT_SECRET"]
    for key, port in (("AUTH", 3001), ("USER", 3002), ("NOTIFICATION", 3006)):
        assert environments["message-service"][key + "_SERVICE_URL"] == (
            f"http://{key.lower()}-service:{port}"
        )
    save("health-matrix.json", results)
    print("PASS: ten Python backends healthy/ready with original DB names and shared uploads")


def main():
    global ARTIFACTS
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, default=ARTIFACTS)
    parser.add_argument("--preservation", action="store_true")
    parser.add_argument("--files", action="store_true")
    parser.add_argument("--runtime", action="store_true")
    args = parser.parse_args()
    ARTIFACTS = args.directory.resolve()
    assert ARTIFACTS.is_relative_to(ROOT / ".artifacts")
    for selected, operation in (
        (args.preservation, preservation),
        (args.files, files),
        (args.runtime, runtime),
    ):
        if selected:
            operation()


if __name__ == "__main__":
    main()
