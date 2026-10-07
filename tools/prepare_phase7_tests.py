"""Own an empty Search shadow; refuse existing schemas without an ownership record."""

import argparse
import json
import time
from pathlib import Path

from verify_runtime import command, select

ARTIFACTS = Path(__file__).resolve().parents[1] / ".artifacts/phase7"
DATABASE = "phase7_search_e2e"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ready", action="store_true")
    args = parser.parse_args()
    if args.ready:
        for _ in range(40):
            try:
                command(
                    [
                        "docker",
                        "exec",
                        "search-service",
                        "python",
                        "-c",
                        "import urllib.request; assert urllib.request.urlopen('http://127.0.0.1:3008/ready',timeout=3).status==200",
                    ]
                )
                print("Search ready")
                return
            except RuntimeError:
                time.sleep(1)
        raise RuntimeError("Search readiness timeout")
    owner = ARTIFACTS / "test-databases.json"
    owned = json.loads(owner.read_text()) if owner.exists() else []
    exists = (
        select(
            "search",
            f"SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='{DATABASE}'",
        ).strip()
        == "1"
    )
    assert not exists or DATABASE in owned, "Refuse unowned Search schema"
    if DATABASE not in owned:
        owned.append(DATABASE)
        owner.parent.mkdir(parents=True, exist_ok=True)
        owner.write_text(json.dumps(owned), encoding="utf-8")
    select(
        "search",
        f"CREATE DATABASE IF NOT EXISTS {DATABASE}; "
        f"CREATE TABLE IF NOT EXISTS {DATABASE}.searchindices LIKE search_db.searchindices",
    )
    print("Prepared owned Search shadow; canonical projection untouched")


if __name__ == "__main__":
    main()
