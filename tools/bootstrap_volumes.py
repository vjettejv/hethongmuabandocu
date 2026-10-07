"""List external local volumes, optionally create missing volumes without touching existing data."""

import argparse
import re
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--create-missing", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    names = re.findall(
        r"^    name: (kientrucpm_[a-z_]+)$",
        (root / "docker-compose.yml").read_text(encoding="utf-8"),
        re.M,
    )
    assert len(names) == len(set(names)) == 9, "Unexpected canonical external volume list"
    existing = set(
        subprocess.check_output(
            ["docker", "volume", "ls", "--format", "{{.Name}}"], text=True, encoding="utf-8"
        ).splitlines()
    )
    missing = sorted(set(names) - existing)
    if args.create_missing:
        for name in missing:
            subprocess.run(["docker", "volume", "create", name], check=True, capture_output=True)
        print(f"Created {len(missing)} missing volumes; existing volumes untouched")
    else:
        print("Missing external volumes:", ", ".join(missing) or "none")


if __name__ == "__main__":
    main()
