"""Owned schema-only fixtures; never reset IDs or mutate a canonical schema."""

import json
from pathlib import Path

from verify_runtime import select

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / ".artifacts/phase5/test-databases.json"
CLONES = [
    (kind, f"phase5_{kind}_{runtime}", [table])
    for kind, table in [
        ("favorite", "favorites"),
        ("review", "reviews"),
        ("search", "searchindices"),
    ]
    for runtime in ("node", "python")
]
CLONES += [
    ("post", "phase5_post_test", ["posts", "images"]),
    ("message", "phase5_message_test", ["messages", "notifications"]),
    ("search", "phase5_search_e2e", ["searchindices"]),
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
            raise RuntimeError("Refusing existing unowned schema")
        if database not in owned:
            owned.append(database)
            OWNER.write_text(json.dumps(owned, indent=2) + "\n")
        select(kind, f"CREATE DATABASE IF NOT EXISTS `{database}`")
        for table in tables:
            select(
                kind,
                f"CREATE TABLE IF NOT EXISTS `{database}`.`{table}` LIKE `{kind}_db`.`{table}`",
            )
        if (
            kind == "post"
            and select(
                kind,
                "SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS "
                f"WHERE CONSTRAINT_SCHEMA='{database}'",
            ).strip()
            == "0"
        ):
            select(
                kind,
                f"ALTER TABLE `{database}`.images ADD CONSTRAINT images_post_fk "
                f"FOREIGN KEY(postId) REFERENCES `{database}`.posts(id) "
                "ON DELETE CASCADE ON UPDATE CASCADE",
            )
        print("Prepared owned schema:", database)


if __name__ == "__main__":
    main()
