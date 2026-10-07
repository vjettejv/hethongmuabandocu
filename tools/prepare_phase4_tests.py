"""Owned empty clones only; never migrate, sync or reset a legacy database."""

import json
from pathlib import Path

from verify_runtime import select

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / ".artifacts/phase4/test-databases.json"
CLONES = [
    (kind, f"phase4_{kind}_{runtime}", tables)
    for kind, tables in [
        ("post", ["posts", "images"]),
        ("search", ["searchindices"]),
        ("message", ["messages", "notifications"]),
    ]
    for runtime in ("node", "python")
]
CLONES += [("favorite", "phase4_favorite_test", ["favorites"])]


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
            raise RuntimeError(f"Refusing unowned database: {database}")
        if database not in owned:
            owned.append(database)
            OWNER.parent.mkdir(parents=True, exist_ok=True)
            OWNER.write_text(json.dumps(owned, indent=2) + "\n")
        select(kind, f"CREATE DATABASE IF NOT EXISTS `{database}`")
        for table in tables:
            select(
                kind,
                f"CREATE TABLE IF NOT EXISTS `{database}`.`{table}` LIKE `{kind}_db`.`{table}`",
            )
        if kind == "post":
            constraint = select(
                kind,
                "SELECT COUNT(*) FROM information_schema."
                "REFERENTIAL_CONSTRAINTS "
                f"WHERE CONSTRAINT_SCHEMA='{database}'",
            ).strip()
            if constraint == "0":
                select(
                    kind,
                    f"ALTER TABLE `{database}`.images ADD CONSTRAINT images_post_fk "
                    "FOREIGN KEY (postId) REFERENCES "
                    f"`{database}`.posts(id) ON DELETE CASCADE ON UPDATE CASCADE",
                )
        print(f"Prepared owned empty clone: {database}")


if __name__ == "__main__":
    main()
