"""Read-only projection drift audit; report counts and hashes, never user content."""

import argparse
import hashlib
import json
from decimal import Decimal
from pathlib import Path

from verify_runtime import select


def records(kind, table, fields):
    pairs = ",".join(f"'{field}',`{field}`" for field in fields)
    return [
        json.loads(line)
        for line in select(
            kind, f"SET NAMES utf8mb4; SELECT JSON_OBJECT({pairs}) FROM `{kind}_db`.`{table}`"
        ).splitlines()
    ]


def audit():
    fields = ("title", "description", "price", "categoryId", "status")
    posts = {row["id"]: row for row in records("post", "posts", ("id", *fields))}
    indices = records(
        "search",
        "searchindices",
        ("postId", *fields, "imageUrl", "categoryName", "createdAt", "updatedAt"),
    )
    projections = {row["postId"]: row for row in indices}
    categories = {
        row["id"]: row["name"] for row in records("category", "categories", ("id", "name"))
    }
    images = {}
    for row in records("post", "images", ("id", "postId", "imageUrl")):
        images.setdefault(row["postId"], set()).add(row["imageUrl"])
    mismatches = {field: 0 for field in (*fields, "imageUrl", "categoryName")}
    ambiguous = 0
    for identifier, row in projections.items():
        if identifier not in posts:
            continue
        post = posts[identifier]
        for field in fields:
            left, right = post[field], row[field]
            if field == "price" and left is not None and right is not None:
                left, right = Decimal(str(left)), Decimal(str(right))
            mismatches[field] += left != right
        urls = images.get(identifier, set())
        if len(urls) > 1:
            ambiguous += 1
        else:
            mismatches["imageUrl"] += row["imageUrl"] != next(iter(urls), None)
        mismatches["categoryName"] += row["categoryName"] != categories.get(
            post["categoryId"], "Đang cập nhật"
        )
    serialized = json.dumps(
        sorted(indices, key=lambda row: row["postId"]),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "mode": "read-only",
        "reconciliationPerformed": False,
        "postCount": len(posts),
        "searchCount": len(indices),
        "approvedPostsMissing": sum(
            row["status"] == "approved" and identifier not in projections
            for identifier, row in posts.items()
        ),
        "orphanSearchRows": len(set(projections) - set(posts)),
        "matchedPostRows": len(set(projections) & set(posts)),
        "fieldMismatches": mismatches,
        "imageRowsAmbiguous": ambiguous,
        "searchContentSha256": hashlib.sha256(serialized.encode()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--compare", type=Path)
    arguments = parser.parse_args()
    current = audit()
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    if arguments.compare:
        assert current == json.loads(arguments.compare.read_text(encoding="utf-8-sig")), (
            "Pre-existing Search projection content/drift changed"
        )
        print("PASS: Search content hash and all pre-existing drift counts unchanged")
    else:
        print(json.dumps(current, indent=2))


if __name__ == "__main__":
    main()
