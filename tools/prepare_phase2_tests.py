"""Create empty schema-only test clones, refusing pre-existing unowned databases."""

import json
from pathlib import Path

from verify_runtime import select

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / ".artifacts/phase2/test-databases.json"
CLONES = [
    ("auth", "phase2_auth_node", "auth_db", "users"),
    ("auth", "phase2_auth_python", "auth_db", "users"),
    ("user", "phase2_user_test", "user_db", "userprofiles"),
]


def main():
    owned = json.loads(OWNER.read_text()) if OWNER.exists() else []
    for container, database, source, table in CLONES:
        existing = (
            select(
                container,
                f"SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='{database}'",
            ).strip()
            == "1"
        )
        if existing and database not in owned:
            raise RuntimeError(f"Refusing pre-existing unowned test database: {database}")
        if database not in owned:
            owned.append(database)
            OWNER.parent.mkdir(parents=True, exist_ok=True)
            OWNER.write_text(json.dumps(owned, indent=2) + "\n")
        select(
            container,
            f"CREATE DATABASE IF NOT EXISTS `{database}`; "
            f"CREATE TABLE IF NOT EXISTS `{database}`.`{table}` "
            f"LIKE `{source}`.`{table}`",
        )
        print(f"Prepared isolated schema clone: {database}.{table}")


if __name__ == "__main__":
    main()
