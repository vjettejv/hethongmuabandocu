"""Read-only full-row hashes for database preservation checks."""

import hashlib
import json
import re

from verify_runtime import select


def content_snapshot(directory):
    schemas = json.loads((directory / "db-before.json").read_text(encoding="utf-8-sig"))
    result = {}
    for database, info in schemas.items():
        kind = database.removesuffix("_db")
        for table in info["tables"]:
            columns = select(
                kind,
                "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                f"WHERE TABLE_SCHEMA='{database}' AND TABLE_NAME='{table}' "
                "ORDER BY ORDINAL_POSITION",
            ).splitlines()
            assert all(re.fullmatch(r"[A-Za-z0-9_]+", name) for name in columns)
            expression = ",".join(f"`{column}`" for column in columns)
            rows = select(
                kind,
                f"SET NAMES utf8mb4; SELECT JSON_ARRAY({expression}) FROM `{database}`.`{table}`",
            ).splitlines()
            digest = hashlib.sha256("\n".join(sorted(rows)).encode()).hexdigest()
            result[f"{database}.{table}"] = {"count": len(rows), "contentSha256": digest}
    return result
