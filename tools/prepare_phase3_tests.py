"""Explicit empty schema clones; refuse pre-existing databases without task ownership."""

import json
from pathlib import Path

from verify_runtime import select

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / ".artifacts/phase3/test-databases.json"
CLONES = [
    ("user", "phase3_user_node", ["userprofiles"]),
    ("user", "phase3_user_python", ["userprofiles"]),
    ("category", "phase3_category_node", ["categories"]),
    ("category", "phase3_category_python", ["categories"]),
    ("post", "phase3_post_test", ["posts", "images"]),
    ("message", "phase3_message_test", ["messages", "notifications"]),
]


def main():
    owned = json.loads(OWNER.read_text()) if OWNER.exists() else []
    for container, database, tables in CLONES:
        exists = (
            select(
                container,
                f"SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='{database}'",
            ).strip()
            == "1"
        )
        if exists and database not in owned:
            raise RuntimeError(f"Refusing pre-existing unowned database: {database}")
        if database not in owned:
            owned.append(database)
            OWNER.parent.mkdir(parents=True, exist_ok=True)
            OWNER.write_text(json.dumps(owned, indent=2) + "\n")
        select(container, f"CREATE DATABASE IF NOT EXISTS `{database}`")
        for table in tables:
            select(
                container,
                f"CREATE TABLE IF NOT EXISTS `{database}`.`{table}` "
                f"LIKE `{container}_db`.`{table}`",
            )
        print(f"Prepared isolated schema clone: {database}")


if __name__ == "__main__":
    main()
