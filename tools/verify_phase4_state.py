"""Phase 4 preservation, runtime wiring and reviewable file manifest."""

import hashlib
import json
import subprocess
from pathlib import Path

from verify_runtime import command

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    "post-service/.env.example",
    "post-service/common/logging.py",
    "post-service/config/settings.py",
    "post-service/config/urls.py",
    "post-service/config/wsgi.py",
    "post-service/requirements.txt",
    "post-service/requirements.lock.txt",
    "post-service/tests/test_health.py",
}


def file_changes():
    before = json.loads((ROOT / ".artifacts/phase4/before-filehashes.json").read_text())
    names = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    ).splitlines()
    modified = []
    for name, digest in before.items():
        path = ROOT / name
        assert path.is_file(), "Pre-existing repository file missing"
        if hashlib.sha256(path.read_bytes()).hexdigest().upper() != digest.upper():
            modified.append(name)
    assert set(modified) <= ALLOWED, "Unexpected modification outside Post foundation"
    assert "HUONG_DAN_TRIEN_KHAI.md" not in modified
    staged = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True
    ).strip()
    assert not staged, "Unexpected staged changes"
    created = sorted(set(names) - set(before))
    value = {
        "created": created,
        "modified": sorted(modified),
        "baselineFiles": len(before),
        "preserved": len(before) - len(modified),
    }
    (ROOT / ".artifacts/phase4/file-changes.json").write_text(json.dumps(value, indent=2) + "\n")
    sections = [
        "# Phase 4 file manifest\n",
        f"Compared with the {len(before)}-file pre-Phase-4 snapshot. "
        f"Created: {len(created)}; modified: {len(modified)}.\n",
        "All other baseline files, including Node/frontend/Phase 1–3 code and "
        "HUONG_DAN_TRIEN_KHAI.md, retain their starting SHA256. "
        "No staged changes or commits were made.\n",
    ]
    for title, files in [("Created", created), ("Modified", sorted(modified))]:
        sections.extend([f"## {title}\n", "```text\n" + "\n".join(files) + "\n```\n"])
    (ROOT / "docs/migration/phase-4-files.md").write_text("\n".join(sections), encoding="utf-8")
    print(
        f"PASS: {len(before) - len(modified)} baseline files unchanged; "
        f"{len(modified)} permitted Post foundation edits; {len(created)} new Phase 4 files"
    )


def runtime():
    before = json.loads((ROOT / ".artifacts/phase4/preserved-runtime.json").read_text())
    for service, expected in before.items():
        current = command(
            ["docker", "inspect", service, "--format", "{{.Id}} {{.Image}} {{.State.StartedAt}}"]
        ).strip()
        assert current == expected, "A preserved canonical container changed"
    rows = json.loads(
        command(
            [
                "docker",
                "inspect",
                "post-service",
                "review-service",
                "auth-service",
                "user-service",
                "favorite-service",
            ]
        )
    )
    post, review, auth, user, favorite = rows
    assert post["Config"]["Image"] == "kientrucpm-post-python-phase4"
    assert post["State"]["Health"]["Status"] == "healthy"
    assert any("gunicorn" in arg for arg in post["Config"]["Cmd"])

    def upload(container):
        mounts = [mount for mount in container["Mounts"] if mount["Destination"] == "/app/uploads"]
        assert len(mounts) == 1 and mounts[0]["Type"] == "volume" and mounts[0]["RW"]
        return mounts[0]["Name"]

    assert upload(post) == upload(review) == "kientrucpm_shared_uploads"
    assert len(post["Mounts"]) == 1

    def environment(container):
        return dict(item.split("=", 1) for item in container["Config"]["Env"] if "=" in item)

    settings = environment(post)
    assert settings["PORT"] == "3003" and settings["DB_NAME"] == "post_db"
    assert settings["CATEGORY_SERVICE_URL"] == "http://category-service:3004"
    assert settings["SEARCH_SERVICE_URL"] == "http://search-service:3008"
    assert settings["MESSAGE_SERVICE_URL"] == "http://message-service:3005"
    assert not settings.get("NODE_OPTIONS")
    assert settings["JWT_SECRET"] == environment(auth)["JWT_SECRET"]
    assert settings["JWT_SECRET"] == environment(user)["JWT_SECRET"]
    assert settings["JWT_SECRET"] == environment(favorite)["JWT_SECRET"]
    assert settings["JWT_SECRET"]
    print(
        "PASS: canonical Django Post, original shared volume, canonical HTTP URLs, "
        "shared JWT; eight preserved container IDs/images/start times unchanged"
    )


def main():
    file_changes()
    runtime()


if __name__ == "__main__":
    main()
