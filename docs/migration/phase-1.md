# Phase 1: Python foundations alongside Node

Baseline: `develop`, commit `92777b8f70b6717e3ffd12657c725b2ea4e3d0ab`.
The pre-existing untracked `HUONG_DAN_TRIEN_KHAI.md` is outside this change.

## Scope

Nine independent Django 5.2/DRF projects and one FastAPI project now live alongside
their Node implementations. Only `/health`, `/ready`, and OpenAPI/documentation
routes are implemented. No business routes, models, JWT verification, email delivery,
uploads, search implementation, realtime, Redis, Celery, or CI/CD have been migrated.

Node remains the business reference. Its source, manifests, Dockerfiles, frontend,
SQL seeds and import scripts remain unchanged. The baseline Compose file is unchanged.

## Services

| Temporary Compose service | Final service | Internal port | Database | App skeleton |
|---|---|---:|---|---|
| api-gateway-python | api-gateway | 3000 | None | FastAPI app |
| auth-service-python | auth-service | 3001 | auth_db | authentication |
| user-service-python | user-service | 3002 | user_db | profiles |
| post-service-python | post-service | 3003 | post_db | posts |
| category-service-python | category-service | 3004 | category_db | categories |
| message-service-python | message-service | 3005 | message_db | messaging |
| notification-service-python | notification-service | 3006 | None | email_delivery |
| review-service-python | review-service | 3007 | review_db | reviews |
| search-service-python | search-service | 3008 | search_db | search_app |
| favorite-service-python | favorite-service | 3009 | favorite_db | favorites |

`search_app` avoids an ambiguous top-level Python module name. In-app notifications
remain owned by Message; Notification is the email delivery boundary and has no DB.

Each Django project contains its own small `common` module so images build independently
without importing another service's code. Changes to common foundation behavior should
be applied consistently across all nine projects.

## Docker coexistence

Use **both** Compose files. `docker-compose.python.yml` is additive and is not a
standalone replacement for the Node configuration. It adds ten `*-python` services,
without overriding canonical Node service names, DB definitions, networks or volumes.

Python containers use the existing `do-cu-micro-net` Compose network and existing
database containers. They publish **no host ports** and specify no fixed container
names. Their processes retain internal ports 3000–3009.

Use the original Compose project name (normally `kientrucpm`) to reuse existing volumes.
Do not switch to a new `-p` project for baseline verification.

Post and Review mount `shared_uploads:/app/uploads:ro` during Phase 1. No upload handlers
exist yet. The read-only mount protects current images; changing it to writable belongs
to the upload migration phase. `/uploads/<filename>` remains the future URL contract.

Docker selects `Dockerfile.python.dockerignore` when using `Dockerfile.python`.
That whitelist includes only Python foundation files, tests and dependency locks;
Node source, environment files and node_modules are excluded from Python contexts.

DB-backed images build mysqlclient with GCC/pkg-config/MySQL development headers in
a build stage, then retain only the MariaDB runtime library in the final image.
Django uses Gunicorn; the gateway uses Uvicorn. No startup command runs migrate,
makemigrations, flush, seed imports or schema synchronization.

## Environment

Copy `.env.python.example` to the ignored `.env.python` and fill in:

- `PYTHON_SECRET_KEY`: a new random Django foundation key; it is unrelated to JWT.
- `PYTHON_DB_USER`, `PYTHON_DB_PASSWORD`: credentials for the existing DBs.
- `PYTHON_CORS_ALLOWED_ORIGINS`: explicit comma-separated local origins.

Do not copy real credentials into `.env.example` or commit `.env.python`.
Existing secret debt remains in legacy Node config; no credential rotation is done here.

Every service also has its own `.env.example` for direct local execution. Django reads
its local `.env` with process environment taking precedence. DB settings support
`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_CONNECT_TIMEOUT`.
Container DB connections use `<service>-db:3306`, not the host mappings 3307–3314.

Canonical service URLs are prepared in env configuration and continue pointing to Node:
`http://auth-service:3001` through `http://favorite-service:3009`. Python source does not
hardcode these internal HTTP URLs. JWT/SMTP example variables are preparation only;
there is no Python auth or email business implementation in this phase.

## Local verification

Use Python **3.12** in an isolated virtual environment. On Windows, when available:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock.txt
.\.venv\Scripts\python.exe tools/verify_foundation.py
```

On Unix:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock.txt
.venv/bin/python tools/verify_foundation.py
```

The verifier runs Ruff, format checking, nine Django checks, ten independent service
pytest suites and contract tests. Independent subprocesses avoid collisions among
the service-local `config` and `common` packages. It provides a generated test key,
disables bytecode writes, and sets unusable DB credentials/port. Tests mock DB access,
do not request pytest-django database fixtures and do not create/drop a test DB.

The development lock pins Linux and Windows dependencies. Each runtime lock pins
the complete Python 3.12/Linux dependency graph. Top-level requirements contain exact
versions verified on PyPI. `tools/lock_foundation.py` refreshes locks from an already
resolved isolated environment; it does not update packages itself.

## Docker verification and startup

Commands below assume `.env.python` is filled in. Do not run bare `up` on the merged
configuration: explicitly select the foundation services to avoid starting Node
processes that perform Sequelize schema synchronization.

```sh
docker compose -f docker-compose.yml config --quiet
docker compose --env-file .env.python -f docker-compose.yml -f docker-compose.python.yml config --quiet

docker compose -f docker-compose.yml up -d --no-deps auth-db user-db post-db category-db message-db review-db search-db favorite-db

python tools/verify_runtime.py --snapshot .artifacts/phase1/db-before.json

docker compose --env-file .env.python -f docker-compose.yml -f docker-compose.python.yml build api-gateway-python auth-service-python user-service-python post-service-python category-service-python message-service-python notification-service-python review-service-python search-service-python favorite-service-python

docker compose --env-file .env.python -f docker-compose.yml -f docker-compose.python.yml up -d --no-deps api-gateway-python auth-service-python user-service-python post-service-python category-service-python message-service-python notification-service-python review-service-python search-service-python favorite-service-python

python tools/verify_runtime.py --http --compare .artifacts/phase1/db-before.json
```

The snapshot tool uses read-only information_schema queries and row counts. It does
not read passwords, JWTs or message contents. It reads each existing MySQL container's
credential inside the container, without printing it. Schema hashes cover columns,
indexes, constraints, foreign-key rules and MySQL case mode. Counts are an additional
data safety check, not a claim that every stored value was hashed.

The MySQL baseline still has no Docker healthchecks. It is not rewritten here.
Python `/ready` exposes connection state, and DB connect attempts have a bounded
timeout. The process boots without an unbounded DB-wait loop.

## Foundation endpoint conventions

| Endpoint | Behavior |
|---|---|
| GET /health | 200 JSON `{service,status:"healthy"}`; no DB or JWT |
| GET /ready, DB-backed | `SELECT 1`; 200 connected, 503 unavailable |
| GET /ready, Notification/Gateway | 200 process/config readiness; no email or DB |
| Django /schema/, /docs/ | OpenAPI + Swagger for health and ready only |
| Gateway /openapi.json, /docs | OpenAPI + Swagger for health and ready only |

Health and readiness have no trailing slash or redirects. Swagger pages may load
their standard UI assets from a CDN. No business schema is fabricated.

Request middleware preserves safe `X-Request-ID` values up to 128 ASCII characters
(`letters/digits/._:-`), generates a UUID for missing/invalid values, and returns the
ID in responses. JSON console request logs include timestamp, level, service,
request_id, method, path, status_code and duration_ms. Request body, query string,
Authorization and DB exception details are not logged by foundation request logging.

CORS uses an explicit env allowlist and exposes X-Request-ID. This is foundation
configuration, not a frontend cutover or a legacy security behavior change.

## Database and contract safety

No business models or migrations exist yet. Django contrib auth/session/contenttypes
apps are not enabled, and default DRF unauthenticated user resolution is disabled.
Notification has no application database. Do not run legacy import scripts to setup
Django, and do not run migrate against baseline DBs to make health work.

See [table mappings](table-mapping.md), [security debt](security-debt.md),
[compatibility notes](compatibility-notes.md), [contracts](../../contracts/README.md)
and [verification results](phase-1-verification.md).

## Phase 2

Implement gateway proxy routing and Auth business logic only in the next phase.
First use contract fixtures and synthetic bcrypt/JWT interoperability tests.
Keep Node dependencies reachable until each controlled service cutover is validated.
Socket.IO adaptation remains a Phase 6 decision. CI/CD remains Phase 8.

Runtime verification completed after Docker recovery on 2026-10-06 (Asia/Saigon).
See [Phase 2 preparation](phase-2-readiness.md) for Gateway + Auth implementation
order, contract checks and isolated data boundaries.
