"""Real MySQL normalization/rollback and Django API smoke in disposable UUID databases."""

import json
import subprocess
from uuid import uuid4

from normalize_post_statuses import REMOTE, target_statuses
from verify_runtime import select


def execute(service, database, code, payload=None, succeeds=True):
    result = subprocess.run(
        ["docker", "exec", "-i", "-e", f"DB_NAME={database}", service, "python", "-c", code],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    if succeeds and result.returncode:
        raise RuntimeError(f"Isolated {service} smoke failed (no credential/SQL output exposed)")
    if not succeeds:
        assert result.returncode != 0, "Concurrent-change guard did not reject mismatch"
        return None
    return json.loads(result.stdout)


API_SMOKE = r"""
import os,json
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from django.conf import settings
from rest_framework.test import APIClient
from posts import clients
from posts.models import Post
import jwt
events=[]
clients.categories=lambda _: {}
clients.dispatch=lambda *args: events.append(args)
client=APIClient()
client.credentials(HTTP_AUTHORIZATION="Bearer " + jwt.encode(
    {"id":18,"roleId":2},settings.JWT_SECRET,algorithm="HS256"))
created=client.post("/",{"title":"isolated moderation smoke","categoryId":1,
    "price":"12.34","status":"approved"},format="json")
assert created.status_code==201
pk=created.json()["post"]["id"]
assert Post.objects.get(pk=pk).status=="pending"
assert events[-1][2]["status"]=="pending"
for decision in ("approved","rejected"):
    response=client.put(f"/admin/posts/{pk}",{"status":decision},format="json")
    assert response.status_code==200 and Post.objects.get(pk=pk).status==decision
    assert events[-2][2]["status"]==decision and events[-1][0]=="MESSAGE"
    count=sum(event[0]=="MESSAGE" for event in events)
    assert client.put(f"/admin/posts/{pk}",{"status":decision},format="json").status_code==200
    assert sum(event[0]=="MESSAGE" for event in events)==count
for invalid in ("available","pending","custom","deleted",None,[],{}):
    count=len(events)
    response=client.put(f"/admin/posts/{pk}",{"status":invalid},format="json")
    assert response.status_code==400
    assert Post.objects.get(pk=pk).status=="rejected" and len(events)==count
assert client.delete(f"/{pk}").status_code==200
assert events[-1][2]["status"]=="deleted"
print(json.dumps({"api":"PASS: create, decisions, repeat, invalid inputs, deletion marker"}))
"""


def main():
    suffix = uuid4().hex
    databases = {kind: "status_smoke_" + kind + "_" + suffix for kind in ("post", "search")}
    created = []
    try:
        for kind, name in databases.items():
            select(kind, f"CREATE DATABASE `{name}`")
            created.append(kind)
            table = "posts" if kind == "post" else "searchindices"
            select(kind, f"CREATE TABLE `{name}`.`{table}` LIKE `{kind}_db`.`{table}`")
        post_db, search_db = databases["post"], databases["search"]
        select("post", f"CREATE TABLE `{post_db}`.images LIKE post_db.images")
        select("post", f"ALTER TABLE `{post_db}`.posts ALTER COLUMN status SET DEFAULT 'available'")
        for identifier, status in enumerate(("available", "pending", "approved", "rejected"), 1):
            select(
                "post",
                f"INSERT INTO `{post_db}`.posts "
                "(id,userId,categoryId,title,description,price,status,`condition`,"
                "createdAt,updatedAt) "
                f"VALUES ({identifier},18,1,'owned smoke','preserve me',12.34,'{status}',"
                "'used','2026-01-01','2026-01-02')",
            )
        for identifier, status in (
            (1, "available"),
            (3, "approved"),
            (9, "deleted"),
            (99, "available"),
        ):
            select(
                "search",
                f"INSERT INTO `{search_db}`.searchindices "
                "(postId,title,description,price,status,createdAt,updatedAt) "
                f"VALUES ({identifier},'owned smoke','preserve me',12.34,'{status}',"
                "'2026-01-01','2026-01-02')",
            )
        for kind, database in databases.items():
            service = kind + "-service"
            payload = {"service": service, "mode": "snapshot"}
            before = execute(service, database, REMOTE, payload)
            target = target_statuses(before["statuses"])
            default = "pending" if kind == "post" else before["default"]
            bad = {**before, "non_status_hash": "concurrent-change"}
            execute(
                service,
                database,
                REMOTE,
                {
                    "service": service,
                    "mode": "apply",
                    "expected": bad,
                    "target": target,
                    "default": default,
                },
                succeeds=False,
            )
            assert execute(service, database, REMOTE, payload) == before
            after = execute(
                service,
                database,
                REMOTE,
                {
                    "service": service,
                    "mode": "apply",
                    "expected": before,
                    "target": target,
                    "default": default,
                },
            )
            assert after["non_status_hash"] == before["non_status_hash"]
            assert after["statuses"] == target and after["default"] == default
            repeated = execute(
                service,
                database,
                REMOTE,
                {
                    "service": service,
                    "mode": "apply",
                    "expected": after,
                    "target": target,
                    "default": default,
                },
            )
            assert repeated == after
            rollback = execute(
                service,
                database,
                REMOTE,
                {
                    "service": service,
                    "mode": "rollback",
                    "expected": after,
                    "target": before["statuses"],
                    "default": before["default"],
                },
            )
            assert rollback == before
            print(f"PASS: {kind} migration, guard, idempotence, exact rollback; row data preserved")
        print(execute("post-service", post_db, API_SMOKE))
    finally:
        for kind in reversed(created):
            name = databases[kind]
            assert name == "status_smoke_" + kind + "_" + suffix
            assert len(suffix) == 32 and all(c in "0123456789abcdef" for c in suffix)
            select(kind, f"DROP DATABASE `{name}`")
            print(f"Cleaned disposable {kind} smoke database")


if __name__ == "__main__":
    main()
