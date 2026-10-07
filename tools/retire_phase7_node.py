"""Execute the reviewed manifest only after integration/recovery/preservation gates."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from legacy_reference import BASELINE, read
from verify_phase7_state import preservation

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / ".artifacts/phase7"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    requirements = {
        "foundation-gate-current.log": "Foundation verification: 22/22 commands passed.",
        **{
            f"regression-phase{phase}.log": f"{count} passed"
            for phase, count in ((2, 35), (3, 51), (4, 97), (5, 103), (6, 87))
        },
        "integration-gate.log": "48 passed",
        "integration-consolidated.log": "48 passed",
    }
    for filename, expected in requirements.items():
        text = (ARTIFACTS / filename).read_text(encoding="utf-8-sig")
        assert expected in text and "FAILED " not in text, "Gate failed: " + filename
    assert len(json.loads((ARTIFACTS / "rollback-checks.json").read_text())) == 4
    assert len(json.loads((ARTIFACTS / "e2e-checks.json").read_text())) >= 14
    assert (ROOT / "docs/migration/phase-7-node-retirement-manifest.md").is_file()
    rows = json.loads((ARTIFACTS / "retirement.json").read_text())
    assert len({row["path"] for row in rows}) == len(rows)
    for row in rows:
        path = (ROOT / row["path"]).resolve()
        assert path.is_relative_to(ROOT) and path.is_file()
        assert not row["path"].endswith(".py")
        assert not row["path"].startswith("do-cu-frontend/")
        data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == row["sha256"], "Target changed since review"
        backup = ARTIFACTS / "before-retirement" / row["path"]
        assert backup.read_bytes() == data, "Missing uncommitted recovery copy"
        if row["recovery"] == BASELINE:
            assert data.replace(b"\r\n", b"\n") == read(row["path"]).replace(b"\r\n", b"\n")
        if row["action"] == "promote":
            assert row["replacement"].endswith(("/Dockerfile", "/Dockerfile.dockerignore"))
            target = ROOT / row["replacement"]
            if target.exists():
                backup_target = ARTIFACTS / "before-retirement" / row["replacement"]
                assert target.read_bytes() == backup_target.read_bytes()
    preservation()  # Recheck current data/files, not just a stale success log.
    print(f"PASS: all gates and {len(rows)} manifest targets/recovery bytes verified")
    if not args.execute:
        return
    # Every path is resolved within ROOT above. There is no recursive directory delete.
    for row in rows:
        source = ROOT / row["path"]
        if row["action"] == "promote":
            target = (ROOT / row["replacement"]).resolve()
            assert target.is_relative_to(ROOT)
            shutil.copyfile(source, target)
            if target.name == "Dockerfile.dockerignore":
                text = target.read_text().replace("Dockerfile.python", "Dockerfile")
                target.write_text(text, encoding="utf-8")
        source.unlink()
    # Prune only empty ancestors of manifest-owned files. Coexisting Python or
    # ignored files prevent rmdir; no recursive src-directory deletion is used.
    empty_candidates = set()
    for row in rows:
        parent = (ROOT / row["path"]).parent
        while parent != ROOT and parent.parent != ROOT:
            empty_candidates.add(parent)
            parent = parent.parent
    for directory in sorted(empty_candidates, key=lambda p: len(p.parts), reverse=True):
        assert directory.resolve().is_relative_to(ROOT)
        try:
            directory.rmdir()
        except OSError:
            pass
    compose = ROOT / "docker-compose.yml"
    compose.write_text(
        compose.read_text().replace("Dockerfile.python", "Dockerfile"), encoding="utf-8"
    )
    (ARTIFACTS / "retirement-completed.json").write_text(
        json.dumps({"targets": len(rows), "removed": [row["path"] for row in rows]}, indent=2),
        encoding="utf-8",
    )
    print("Manifest retirement complete; ten canonical Python Dockerfiles promoted")


if __name__ == "__main__":
    main()
