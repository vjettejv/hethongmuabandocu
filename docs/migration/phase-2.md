# Phase 2: FastAPI Gateway + Django Auth

REST now enters the Python Gateway on port 3000. Auth is Django on 3001 and maps
`auth_db.users` without migrations. The eight remaining business services stay Node.
Node sources, package files, legacy Dockerfiles, seeds, frontend and baseline Compose
are preserved. See [implementation report](phase-2-implementation-report.md).

## Runtime

Use the original Compose project name (`kientrucpm`) and existing volumes. Copy
`.env.python.example` to the ignored `.env.python` and fill existing DB credentials,
a Django foundation key and the **existing shared Node JWT key**. JWT_SECRET is
separate from Django SECRET_KEY. Do not rotate the shared JWT key as part of cutover.
Never commit secrets or run a migration/import script to make this stack work.

Use `docker-compose.phase2.yml` with the baseline, instead of the Phase 1 additive
overlay. Canonical DNS names `api-gateway`/`auth-service` now resolve to Python;
`user-service` through `favorite-service` resolve to their Node implementations.
Ports and DB ownership are unchanged. Phase 1 prototypes can be stopped during
cutover; their files and containers do not need to be deleted.

```sh
docker compose -f docker-compose.yml config --quiet
docker compose --env-file .env.python -f docker-compose.yml -f docker-compose.phase2.yml config --quiet
python tools/verify_runtime.py --snapshot .artifacts/phase2/db-before.json
docker compose --env-file .env.python --parallel 1 -f docker-compose.yml -f docker-compose.phase2.yml build api-gateway auth-service
docker compose --env-file .env.python -f docker-compose.yml -f docker-compose.phase2.yml up -d --no-deps api-gateway auth-service user-service post-service category-service message-service notification-service review-service search-service favorite-service
```

The eight existing MySQL containers must already be running before these `--no-deps`
commands. Optional frontend startup uses `up -d --no-deps frontend` with the same files.
After Gateway recreation, **restart an already-running frontend** with
`docker compose --env-file .env.python -f docker-compose.yml -f docker-compose.phase2.yml restart frontend`.
The unchanged Nginx config resolves upstream DNS on startup and can retain the old
container IP; this ordering is required for cutover and rollback. Restarting it
refreshes DNS without editing frontend source.
No `down -v`, volume deletion, schema import or automatic migration is used.

Node services receive a read-only preload, `tools/runtime/legacy-schema-guard.cjs`.
It suppresses Sequelize startup sync and rejects DDL queries. This protects existing
tables without editing Node business source; ordinary ORM reads/writes still work.
Source/server read-only binds ensure cached Node images execute the actual baseline
handlers. Existing MySQL volumes and uploads remain in place.

Notification uses its existing `MOCK_EMAIL=true` mode in this development overlay.
No real email is sent during verification. Real SMTP configuration/production
delivery is not established by the Phase 2 tests.

## Gateway behavior

Generic prefixes strip `/auth`, `/users`, `/posts`, `/categories`, `/messages`,
`/notifications`, `/reviews`, `/search` or `/favorites`. Admin routes, `/uploads`
and `/socket.io` retain the complete path. Legacy aliases remain reachable.
Raw query bytes, multipart boundaries, body streams, response bytes/status,
content/cache headers and repeated headers pass through. Hop-by-hop headers are
removed; Host is set for the upstream. Request ID propagates, forwarding metadata
is appended/set and is never used as trusted identity. No global JWT authorization.

One lifespan-managed httpx AsyncClient provides connection pooling and explicit
connect/read timeouts (env CONNECT_TIMEOUT/READ_TIMEOUT, defaults 5/30 seconds).
Upstream connection errors produce 502 `{"error":"Service Unavailable"}`; timeout
before headers produces 504 `{"error":"Gateway Timeout"}`. A failure after streaming
has started closes the stream; it cannot change the already-sent status.
Upstream redirects are passed through. Gateway neither parses uploads nor stores them.

CORS uses an explicit allowlist and replaces upstream permissive CORS headers with
Gateway policy. Default development origins include Vite, localhost on standard
HTTP port and 127.0.0.1. Standard browser Origin `http://localhost` is distinct from
the explicit `http://localhost:80` spelling, so both are included.

Infrastructure health/readiness and OpenAPI remain Gateway-owned. Auth health,
readiness/schema/docs are available internally and not newly exposed under `/auth`.
Auth Swagger documents the five business endpoints plus its health/ready routes.

## Socket.IO transition

Polling HTTP follows the ordinary streaming proxy to Node Message. WebSocket upgrade
uses a generic bidirectional frame bridge via websockets. Socket.IO and Engine.IO
protocol handling remain entirely in Node Message; no replacement server, Channels
or Redis is introduced. The original frontend Nginx WebSocket location is unchanged.
Tests verify polling, EIO=4 probe/upgrade and Socket.IO namespace connection through
both Gateway and frontend Nginx, then send the existing room-join frame. They do not
claim full message/notification delivery parity or fix room authorization.

## Auth behavior and data mapping

The unmanaged model maps `users`, numeric ID, camelCase DB columns and nullable
legacy role/verification fields. Timestamps are written explicitly; public user
projections expose only id, username, email and roleId. No Django user/session tables.

Registration preserves existing unverified-account reuse and verified duplicate
errors. New passwords use bcrypt cost 10 and the first 72 UTF-8 bytes, matching
bcryptjs. Login accepts username or email, keeps the token/user envelope and does
not require isVerified, matching the baseline. JWT uses env-only HS256 and the
id/roleId/iat/exp claims with 86400-second TTL. No refresh/logout/reset endpoints.

OTP uses a random six-digit value and constant-time comparison with a nonempty stored
OTP. Success saves isVerified/clears OTP before best-effort Node User PUT /{id}
with fullName=username. Registration calls Node Notification POST /email with the
legacy payload. Downstream failures retain successful Auth state/response; calls
have a short env-configured timeout and no automatic write retries.

Intentional differences: no hardcoded OTP bypass; empty/cleared OTP cannot verify;
wrong OTP is 400 with readable error instead of legacy mojibake/500; only Bearer
headers are accepted; DB exceptions are generic 500 without sensitive details.
Login verification enforcement, OTP expiry/rate limiting and unrelated Node
authorization problems remain deferred security debt.

## Verification

```sh
python tools/verify_foundation.py
python tools/prepare_phase2_tests.py
docker compose --env-file .env.python -f docker-compose.yml -f docker-compose.phase2.yml -f docker-compose.phase2.test.yml --profile phase2-test up -d --no-deps auth-reference auth-candidate user-test notification-test proxy-fixture gateway-probe
```

`auth-reference` uses the legacy Node Dockerfile/image and unchanged handlers.
If the reference image is absent, build that service explicitly with the same files.
Only its test transport redirects the hardcoded User URL to `user-test`.
The setup creates three empty, schema-only clones in the existing Auth/User MySQL
containers: phase2_auth_node, phase2_auth_python, phase2_user_test. It refuses an
existing unowned DB. Test endpoints publish random ports on 127.0.0.1 only; no
production/internal service port changes. Tests delete only records in owned clones.

Windows:

```powershell
$env:PHASE2_TEST='1'
.\.venv\Scripts\python.exe -m pytest integration-tests/phase2 -q
.\.venv\Scripts\python.exe tools/verify_phase2_runtime.py
```

Unix:

```sh
PHASE2_TEST=1 .venv/bin/python -m pytest integration-tests/phase2 -q
.venv/bin/python tools/verify_phase2_runtime.py
```

Integration tests compare all five Auth endpoints, response shapes and DB effects,
Node/Python JWT and bcrypt, downstream outages, multipart/binary real wire transport,
CORS, frontend HTTP routing and Socket.IO transition. Frontend must be running for
the Nginx/Socket.IO checks. The E2E verifier creates one owned synthetic account in
legacy Auth, refuses an existing profile slot before OTP, proves Node JWT acceptance,
then removes only its account/profile. It does not reset auto-increment.

The full DB snapshot is compared after cleanup. Schema fingerprints and counts
exclude test-clone schemas and do not hash every stored business value. Local
evidence remains ignored in `.artifacts/phase2/`; no passwords/OTPs/tokens are written
to the E2E ownership record. Stop only the six test services after verification.

## Controlled rollback

An optional final overlay restores Node Gateway/Auth builds while retaining the
Node schema guard: `docker-compose.phase2.rollback.yml`. Its configuration is checked;
rollback is not applied during verification. Do not run the unguarded baseline Auth
startup on legacy DBs. When rollback is deliberately selected, build/start Gateway
and Auth with baseline + Phase 2 + rollback files, using the same env/project/volumes.
Node Gateway's original health/proxy limitations return with that implementation.
Restore Python by rebuilding/starting with baseline + Phase 2 files only.

Phase 3 is User + Category. No implementation of those migrations is included here.
