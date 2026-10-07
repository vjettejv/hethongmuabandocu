"""Normalize legacy moderation statuses with an on-disk journal and guarded rollback.

Default is read-only. --apply updates only status values/defaults; no Search rebuild.
Database credentials stay inside the existing Django containers.
"""

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
SERVICES = {"post-service": ("posts", "id"), "search-service": ("searchindices", "postId")}

REMOTE = r"""
import os, sys, json, hashlib
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from django.db import connection, transaction

data = json.load(sys.stdin)
table, pk = {"post-service": ("posts", "id"),
             "search-service": ("searchindices", "postId")}[data["service"]]

def snapshot(lock=False):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM `" + table + "` ORDER BY `" + pk + "`" +
                       (" FOR UPDATE" if lock else ""))
        names = [col[0] for col in cursor.description]
        rows = [dict(zip(names, row)) for row in cursor.fetchall()]
        cursor.execute("SELECT COLUMN_DEFAULT FROM information_schema.COLUMNS "
                       "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s AND COLUMN_NAME='status'",
                       [table])
        default = cursor.fetchone()[0]
    non_status = [{key: value for key, value in row.items() if key != "status"} for row in rows]
    return {"statuses": {str(row[pk]): row["status"] for row in rows},
            "non_status_hash": hashlib.sha256(json.dumps(non_status, default=str,
                sort_keys=True, ensure_ascii=False).encode()).hexdigest(), "default": default}

mode = data["mode"]
if mode == "snapshot":
    result = snapshot()
else:
    expected = data["expected"]
    with transaction.atomic():
        current = snapshot(lock=True)
        if current != expected:
            raise RuntimeError("Concurrent data/default change; no row update performed")
        target = data["target"]
        if set(target) != set(current["statuses"]):
            raise RuntimeError("Journal ID mismatch")
        updates = [(new, int(key), current["statuses"][key])
                   for key, new in target.items() if new != current["statuses"][key]]
        with connection.cursor() as cursor:
            cursor.executemany("UPDATE `" + table + "` SET status=%s WHERE `" + pk +
                               "`=%s AND status <=> %s", updates)
            if cursor.rowcount != len(updates) and updates:
                raise RuntimeError("Guarded update count mismatch")
    # MySQL ALTER DEFAULT commits implicitly: execute only after the row transaction.
    # Journal is already durable; a partial failure can be resumed or rolled back.
    if table == "posts" and data["default"] != current["default"]:
        if data["default"] not in ("available", "pending"):
            raise RuntimeError("Unsupported journal default")
        with connection.cursor() as cursor:
            cursor.execute("ALTER TABLE posts ALTER COLUMN status SET DEFAULT '" +
                           data["default"] + "'")
    result = snapshot()
    if result["statuses"] != target or result["non_status_hash"] != current["non_status_hash"]:
        raise RuntimeError("Post-update preservation check failed")
print(json.dumps(result))
"""


def remote(service, mode, **payload):
    result = subprocess.run(
        ["docker", "exec", "-i", service, "python", "-c", REMOTE],
        input=json.dumps({"service": service, "mode": mode, **payload}),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=90,
        check=False,
    )
    if result.returncode:
        # Do not print potentially sensitive SQL or application tracebacks.
        raise RuntimeError(f"{service}: {mode} failed; inspect journal before retry/rollback")
    return json.loads(result.stdout)


def target_statuses(statuses):
    return {key: "pending" if value == "available" else value for key, value in statuses.items()}


def save(path, journal):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(journal, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def summary(states):
    for service, state in states.items():
        counts = {}
        for value in state["statuses"].values():
            counts[str(value)] = counts.get(str(value), 0) + 1
        print(json.dumps({"service": service, "counts": counts, "default": state["default"]}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true")
    group.add_argument("--rollback", type=Path, metavar="JOURNAL")
    args = parser.parse_args()
    states = {service: remote(service, "snapshot") for service in SERVICES}
    if args.rollback:
        path = args.rollback.resolve()
        if not path.is_relative_to(ROOT / ".artifacts/post-status-normalization"):
            parser.error("Rollback journal must be inside this workspace's normalization artifacts")
        journal = json.loads(path.read_text(encoding="utf-8"))
        for service in reversed(SERVICES):
            before = journal["before"][service]
            current = states[service]
            if current["non_status_hash"] != before["non_status_hash"]:
                raise RuntimeError(
                    "Business data changed since migration; refusing blanket rollback"
                )
            for key, old in before["statuses"].items():
                if current["statuses"].get(key) not in {old, target_statuses({key: old})[key]}:
                    raise RuntimeError("A moderation decision changed; refusing blanket rollback")
            states[service] = remote(
                service,
                "rollback",
                expected=current,
                target=before["statuses"],
                default=before["default"],
            )
        journal["rolled_back"] = True
        save(path, journal)
    elif args.apply:
        allowed = {"available", "pending", "approved", "rejected"}
        if set(states["post-service"]["statuses"].values()) - allowed:
            raise RuntimeError("Unknown Post statuses; review before normalizing")
        if states["post-service"]["default"] not in {"available", "pending"}:
            raise RuntimeError("Unexpected Post database default")
        folder = (
            ROOT
            / ".artifacts/post-status-normalization"
            / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8])
        )
        folder.mkdir(parents=True)
        path = folder / "journal.json"
        journal = {"before": json.loads(json.dumps(states)), "after": {}, "complete": False}
        save(path, journal)
        print(f"Journal: {path}", flush=True)
        for service, state in states.items():
            states[service] = remote(
                service,
                "apply",
                expected=state,
                target=target_statuses(state["statuses"]),
                default="pending" if service == "post-service" else state["default"],
            )
            journal["after"][service] = states[service]
            save(path, journal)
        journal["complete"] = True
        save(path, journal)
    summary(states)
    print(
        "PASS: status-only normalization"
        if args.apply
        else "Read-only inventory"
        if not args.rollback
        else "PASS: guarded rollback"
    )


if __name__ == "__main__":
    main()
