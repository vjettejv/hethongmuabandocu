"""Run isolated service checks/tests without creating or modifying a database."""

import os
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DJANGO_SERVICES = [
    "auth-service",
    "user-service",
    "post-service",
    "category-service",
    "message-service",
    "notification-service",
    "review-service",
    "search-service",
    "favorite-service",
]


def main():
    environment = os.environ.copy()
    # Unit tests use mocked cursors. Empty credentials prevent incidental live access.
    environment.update(
        SECRET_KEY=secrets.token_urlsafe(48),
        JWT_SECRET=secrets.token_urlsafe(48),
        DEBUG="false",
        PYTHONDONTWRITEBYTECODE="1",
        DB_HOST="127.0.0.1",
        DB_PORT="1",
        DB_USER="",
        DB_PASSWORD="",
        ALLOWED_HOSTS="testserver,localhost",
        CORS_ALLOWED_ORIGINS="http://localhost:5173,http://localhost:80",
    )
    environment.pop("DJANGO_SETTINGS_MODULE", None)
    environment.pop("SERVICE_NAME", None)
    checks = [
        (ROOT, ["-m", "ruff", "check", "."]),
        (ROOT, ["-m", "ruff", "format", "--check", "."]),
    ]
    for service in DJANGO_SERVICES:
        checks += [
            (ROOT / service, ["manage.py", "check"]),
            (ROOT / service, ["-m", "pytest", "-q"]),
        ]
    checks += [
        (ROOT / "api-gateway", ["-c", "import app.main; assert app.main.app"]),
        (ROOT / "api-gateway", ["-m", "pytest", "-q"]),
        (ROOT / "contract-tests", ["-m", "pytest", "-q"]),
    ]
    failures = 0
    for directory, arguments in checks:
        print(f"CHECK {directory.name}: {' '.join(arguments)}", flush=True)
        result = subprocess.run(
            [sys.executable, *arguments], cwd=directory, env=environment, check=False
        )
        if result.returncode:
            failures += 1
    print(f"Foundation verification: {len(checks) - failures}/{len(checks)} commands passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
