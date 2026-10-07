"""Read/export only immutable baseline files without touching the active Git checkout."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "92777b8f70b6717e3ffd12657c725b2ea4e3d0ab"
SERVICES = [
    "api-gateway",
    *[
        kind + "-service"
        for kind in (
            "auth",
            "user",
            "post",
            "category",
            "message",
            "notification",
            "review",
            "search",
            "favorite",
        )
    ],
]


def read(path):
    return subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=ROOT)


def export(destination):
    destination = destination.resolve()
    assert destination.is_relative_to(ROOT / ".artifacts"), "Export only into ignored artifacts"
    assert (
        subprocess.check_output(["git", "cat-file", "-t", BASELINE], cwd=ROOT).strip() == b"commit"
    )
    names = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", BASELINE, "--", *SERVICES],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    ).splitlines()
    hashes = {}
    for name in names:
        path = (destination / name).resolve()
        assert path.is_relative_to(destination)
        data = read(name)
        if path.exists():
            assert path.read_bytes() == data, "Existing reference file differs"
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    (destination / "export-manifest.json").write_text(
        json.dumps({"commit": BASELINE, "sha256": hashes}, indent=2), encoding="utf-8"
    )
    print(
        f"Verified/exported {len(hashes)} immutable baseline backend files; "
        "active checkout untouched"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", type=Path, required=True)
    export(parser.parse_args().export)


if __name__ == "__main__":
    main()
