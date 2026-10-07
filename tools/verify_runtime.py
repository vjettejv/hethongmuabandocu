"""Read-only Docker health/readiness and legacy schema/row-count snapshots."""

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

DATABASES = ["auth", "user", "post", "category", "message", "review", "search", "favorite"]
SERVICES = {
    "api-gateway": 3000,
    "auth-service": 3001,
    "user-service": 3002,
    "post-service": 3003,
    "category-service": 3004,
    "message-service": 3005,
    "notification-service": 3006,
    "review-service": 3007,
    "search-service": 3008,
    "favorite-service": 3009,
}
PROJECT = os.environ.get("COMPOSE_PROJECT_NAME", Path(__file__).resolve().parents[1].name.lower())


def container_name(name):
    """Map canonical names only when the disposable CI runner explicitly opts in."""
    prefix = os.environ.get("CANONICAL_TEST_PREFIX", "")
    if prefix:
        if not re.fullmatch(r"marketplace-ci-[0-9a-f]{12}-", prefix):
            raise RuntimeError("Invalid isolated test container prefix")
        canonical = (
            set(SERVICES) | {"do-cu-frontend-micro"} | {f"do-cu-{kind}-db" for kind in DATABASES}
        )
        if name in canonical:
            return prefix + name
    return name


def command(arguments):
    if arguments[:2] == ["docker", "exec"]:
        arguments = [container_name(value) for value in arguments]
    elif arguments[:2] == ["docker", "inspect"]:
        arguments = [container_name(value) for value in arguments]
    result = subprocess.run(
        arguments, capture_output=True, text=True, encoding="utf-8", timeout=60, check=False
    )
    if result.returncode:
        # Do not echo credentials, DB client stderr or potentially sensitive application logs.
        raise RuntimeError(f"Docker verification command failed (exit {result.returncode}).")
    return result.stdout


def select(database, query):
    container = f"do-cu-{database}-db"
    return command(
        [
            "docker",
            "exec",
            container,
            "sh",
            "-c",
            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" '
            'exec mysql -h127.0.0.1 -uroot --batch --raw --skip-column-names "$@"',
            "mysql-probe",
            "-e",
            query,
        ]
    )


def snapshot():
    result = {}
    for database in DATABASES:
        name = f"{database}_db"
        queries = [
            f"SELECT TABLE_NAME,COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_DEFAULT,EXTRA "
            f"FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='{name}' "
            "ORDER BY TABLE_NAME,ORDINAL_POSITION",
            f"SELECT TABLE_NAME,INDEX_NAME,NON_UNIQUE,SEQ_IN_INDEX,COLUMN_NAME "
            f"FROM information_schema.STATISTICS WHERE TABLE_SCHEMA='{name}' "
            "ORDER BY TABLE_NAME,INDEX_NAME,SEQ_IN_INDEX",
            f"SELECT TABLE_NAME,CONSTRAINT_NAME,CONSTRAINT_TYPE "
            f"FROM information_schema.TABLE_CONSTRAINTS WHERE TABLE_SCHEMA='{name}' "
            "ORDER BY TABLE_NAME,CONSTRAINT_NAME",
            f"SELECT TABLE_NAME,CONSTRAINT_NAME,REFERENCED_TABLE_NAME,UPDATE_RULE,DELETE_RULE "
            f"FROM information_schema.REFERENTIAL_CONSTRAINTS WHERE CONSTRAINT_SCHEMA='{name}' "
            "ORDER BY TABLE_NAME,CONSTRAINT_NAME",
            "SELECT @@lower_case_table_names",
        ]
        tables = select(
            database,
            f"SELECT TABLE_NAME FROM information_schema.TABLES "
            f"WHERE TABLE_SCHEMA='{name}' AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME",
        ).splitlines()
        if not all(re.fullmatch(r"[A-Za-z0-9_]+", table) for table in tables):
            raise RuntimeError("Unexpected table identifier; refusing to build a count query.")
        counts = {
            table: int(select(database, f"SELECT COUNT(*) FROM `{name}`.`{table}`").strip())
            for table in tables
        }
        structure = select(database, ";".join(queries))
        result[name] = {
            "tables": tables,
            "rows": counts,
            "schema_sha256": hashlib.sha256(structure.encode()).hexdigest(),
        }
    return result


def check_http():
    for service, port in SERVICES.items():
        container = command(
            [
                "docker",
                "ps",
                "--filter",
                f"label=com.docker.compose.project={PROJECT}",
                "--filter",
                f"label=com.docker.compose.service={service}",
                "--format",
                "{{.ID}}",
            ]
        ).strip()
        if not container:
            raise RuntimeError(f"Missing canonical container: {service}")
        probe = (
            "import json, urllib.request; "
            f"service={service!r}; port={port}; "
            "results=[]; "
            "\nfor path in ['/health','/ready']:\n"
            " request=urllib.request.Request(f'http://127.0.0.1:{port}{path}', "
            "headers={'X-Request-ID':'phase1-runtime'})\n"
            " with urllib.request.urlopen(request, timeout=8) as response:\n"
            "  data=json.load(response)\n"
            "  assert response.status==200 and data['service']==service\n"
            "  assert data['status']==('healthy' if path=='/health' else 'ready')\n"
            "  assert response.headers['X-Request-ID']=='phase1-runtime'\n"
            "  assert response.headers['Content-Type'].startswith('application/json')\n"
            "  if path=='/ready' and service not in ['api-gateway','notification-service']:\n"
            "   assert data['database']=='connected'\n"
            "  results.append({'path':path,'status':response.status,'body':data})\n"
            "print(json.dumps({'service':service,'checks':results}))"
        )
        print(command(["docker", "exec", container, "python", "-c", probe]).strip())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--compare", type=Path)
    parser.add_argument("--http", action="store_true")
    arguments = parser.parse_args()
    if arguments.snapshot:
        data = snapshot()
        arguments.snapshot.parent.mkdir(parents=True, exist_ok=True)
        arguments.snapshot.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(data, indent=2))
    if arguments.http:
        check_http()
    if arguments.compare:
        before = json.loads(arguments.compare.read_text(encoding="utf-8"))
        if snapshot() != before:
            raise RuntimeError("Legacy schema or row-count snapshot changed.")
        print("PASS: all eight database schemas and row counts unchanged.")


if __name__ == "__main__":
    main()
