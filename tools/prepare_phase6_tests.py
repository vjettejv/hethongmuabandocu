"""Owned schema-only clones; canonical tables and ID counters remain untouched."""

import json
from pathlib import Path

from verify_runtime import select

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / ".artifacts/phase6/test-databases.json"
CLONES = [
    ("message", f"phase6_message_{runtime}", ["messages", "notifications"])
    for runtime in ("node", "python")
]
CLONES += [
    ("auth", "phase6_auth_test", ["users"]),
    ("user", "phase6_user_test", ["userprofiles"]),
    ("post", "phase6_post_test", ["posts", "images"]),
    ("search", "phase6_search_test", ["searchindices"]),
    ("search", "phase6_search_e2e", ["searchindices"]),
]


def main():
    owned = json.loads(OWNER.read_text()) if OWNER.exists() else []
    for kind, database, tables in CLONES:
        exists = (
            select(
                kind,
                f"SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='{database}'",
            ).strip()
            == "1"
        )
        if exists and database not in owned:
            raise RuntimeError("Refuse existing unowned schema")
        if database not in owned:
            owned.append(database)
            OWNER.parent.mkdir(parents=True, exist_ok=True)
            OWNER.write_text(json.dumps(owned, indent=2), encoding="utf-8")
        select(kind, f"CREATE DATABASE IF NOT EXISTS `{database}`")
        for table in tables:
            select(
                kind,
                f"CREATE TABLE IF NOT EXISTS `{database}`.`{table}` LIKE `{kind}_db`.`{table}`",
            )
        print("Prepared owned clone:", database)


if __name__ == "__main__":
    main()
