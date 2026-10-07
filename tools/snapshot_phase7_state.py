"""Capture fresh read-only safety evidence; never overwrite an earlier baseline."""

import argparse
import hashlib
import json
from pathlib import Path

import verify_phase5_state
from verify_phase4_uploads import inventory
from verify_runtime import SERVICES, command, snapshot

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    directory = parser.parse_args().directory.resolve()
    assert directory.is_relative_to(ROOT / ".artifacts")
    assert not (directory / "db-before.json").exists(), "Refuse baseline overwrite"
    directory.mkdir(parents=True, exist_ok=True)

    def save(name, value):
        (directory / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    names = command(["git", "ls-files", "--cached", "--others", "--exclude-standard"]).splitlines()
    save(
        "before-filehashes.json",
        {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in names
            if (ROOT / name).is_file()
        },
    )
    (directory / "git-status-before.txt").write_text(
        command(["git", "status", "--short"]), encoding="utf-8"
    )
    save("db-before.json", snapshot())
    verify_phase5_state.ARTIFACTS = directory
    save("db-content-before.json", verify_phase5_state.content_snapshot())
    save("uploads-before.json", inventory())
    save(
        "volumes-before.json",
        command(["docker", "volume", "ls", "--format", "{{.Name}}"]).splitlines(),
    )
    save(
        "network-before.json",
        json.loads(command(["docker", "network", "inspect", "kientrucpm_do-cu-micro-net"])),
    )
    rows = json.loads(
        command(
            [
                "docker",
                "inspect",
                *SERVICES,
                "do-cu-frontend-micro",
                *[
                    "do-cu-" + kind + "-db"
                    for kind in (
                        "auth",
                        "user",
                        "post",
                        "category",
                        "message",
                        "review",
                        "search",
                        "favorite",
                    )
                ],
            ]
        )
    )
    save(
        "runtime-before.json",
        [
            {
                "name": row["Name"],
                "id": row["Id"],
                "image": row["Image"],
                "mounts": row["Mounts"],
                "ports": row["HostConfig"]["PortBindings"],
            }
            for row in rows
        ],
    )
    print("Fresh eight-DB/upload/files/runtime baseline recorded; secret values withheld")


if __name__ == "__main__":
    main()
