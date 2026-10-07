# Phase 6 operating guide

Message and Notification join the existing Python stack. Message runs Django REST and
python-socketio in the same Uvicorn ASGI process, with **one worker**. Notification is
a DB-less Django service. The original Node sources and images remain available.

## Compose order

Use this order for every canonical operation:

```powershell
$stack = @('-f','docker-compose.yml',
  '-f','docker-compose.phase2.yml','-f','docker-compose.phase3.yml',
  '-f','docker-compose.phase4.yml','-f','docker-compose.phase5.yml',
  '-f','docker-compose.phase6.yml')
docker compose @stack config --quiet
docker compose @stack build message-service notification-service
docker compose @stack up -d --no-deps --no-build message-service notification-service
```

Supply `PYTHON_SECRET_KEY`, shared `JWT_SECRET`, `PYTHON_DB_USER` and
`PYTHON_DB_PASSWORD` privately using the existing deployment environment. Preserve
the existing `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `NODE_ENV` and
`MOCK_EMAIL` values; do not print a resolved Compose configuration. Keep SMTP in mock
mode for migration tests. Images are `kientrucpm-message-python-phase6` and
`kientrucpm-notification-python-phase6`. Dependencies and transitive packages are
pinned in the target service lock files and the development lock.

Message 3005 and Notification 3006 retain internal service ports. Probe `/health`
and `/ready` with `docker exec` inside those containers; use public Gateway 3000
and Nginx 80 for application and Socket.IO E2E checks. Do not publish extra ports
solely for readiness.

Do not use multiple Message workers/replicas: room membership is held in one process.
Scaling requires a deliberate shared adapter/broker design in a later phase.

## Isolated verification

```powershell
.\.venv\Scripts\python.exe tools/verify_foundation.py
.\.venv\Scripts\python.exe tools/prepare_phase6_tests.py
docker compose @stack -f docker-compose.phase6.test.yml --profile phase6-test config --quiet
docker compose @stack -f docker-compose.phase6.test.yml --profile phase6-test up -d --no-deps --no-build <fixture-services>
$env:PHASE6_TEST = '1'
.\.venv\Scripts\python.exe -m pytest -c integration-tests/phase6/pytest.ini integration-tests/phase6 -q
```

Select the 18 service names from `docker-compose.phase6.test.yml` explicitly; do not
start unrelated services. Fixture ports bind only to loopback. Node and Python
Message use distinct owned schema clones. Auth/User/Post/Search use their own clones.
The SMTP sink accepts only synthetic credentials on the Docker network and retains
synthetic deliveries in memory. No real address is used. The Socket.IO test harness
loads the unchanged frontend's installed JavaScript client and verifies actual events.

The `phase6-dependencies.cjs` transport captures synthetic requests and can inject
HTTP/JSON/network failures. Canonical dependencies use direct service DNS, not this
test transport. Cleanup deletes only tables in explicitly owned fixture schemas;
it never drops schemas or resets ID counters.

## Prior-phase regressions

Apply the selected `docker-compose.phaseN.test.yml`, then apply
`docker-compose.phase6.regression.yml` LAST. Phase 4 also needs
`docker-compose.phase5.regression.yml` before the Phase 6 regression overlay. Prepare
the corresponding owned clones, start only that phase's fixtures, run its original
pytest suite with `PHASEN_TEST=1`, and stop those fixtures afterward. Do not edit or
weaken the old assertions. Historical test names that mention Node retain their
names; the candidate Message/Notification image is now Python. Node references used
for differential assertions remain Node.

## Canonical end-to-end verification

Before canonical E2E, capture the eight legacy schema/count/full-row hashes, runtime
identities, upload hashes and Search drift into `.artifacts/phase6`. Do not overwrite
the pre-write baseline. Run `prepare_phase6_tests.py` to create the owned Search schema.

Apply `docker-compose.phase6.e2e.yml` LAST and recreate **only Search** with
`up -d --no-deps --no-build search-service`. This changes Search's test DB setting,
preserving its Python image. Wait for readiness, then run:

```powershell
.\.venv\Scripts\python.exe tools/verify_phase6_runtime.py
```

Always restore Search with the canonical `$stack` in a `finally` block, even when
the E2E command fails. This isolates pre-existing orphan Search projections whose
IDs can collide with a newly created legacy Post ID. Post's image, source, upload
volume and service URLs do not change. Synthetic E2E posts have no images.

The script registers unique `.invalid` accounts, verifies OTPs without printing
them, logs in, creates real profiles, uses the public gateway/Nginx socket endpoints,
and checks message, notification and Post moderation events. It journals only owned
IDs and a UUID marker. Its guarded cleanup removes these exact synthetic records.
Review `.artifacts/phase6/runtime-owned.json` if interrupted; never broadly delete
canonical rows. ID counters may advance naturally; do not reset them.

After restoring Search:

```powershell
.\.venv\Scripts\python.exe tools/verify_phase6_state.py --preservation --runtime --files
.\.venv\Scripts\python.exe tools/audit_phase5_search.py --compare .artifacts/phase6/search-drift-before.json
```

## Rollback

Validate the rollback overlay LAST, then use it only if a rollback is actually needed:

```powershell
docker compose @stack -f docker-compose.phase6.rollback.yml config --quiet
docker compose @stack -f docker-compose.phase6.rollback.yml up -d --no-deps --no-build message-service notification-service
```

This restores only the two original Node images, original commands and read-only
source mounts. The Node Message schema guard suppresses `sequelize.sync()`; Django
never owns migrations for legacy business tables. Phase 2–5 services remain Python.
No live rollback was needed for the migration validation.

## Behavior and limits

REST preserves legacy success/error envelopes and camelCase fields. Sender identity
comes from the existing local HS256 JWT. Contacts retain legacy integer-key ordering,
User enrichment and fallback. Send persists before awaiting receiver Auth/email HTTP,
then emits `receive_message`; email failure does not roll back the message. Offline
messages are retrieved from history; events are not replayed on reconnect.

Static GET `/notifications` now reaches the intended newest-first 50-row handler.
The old Node route was shadowed by `/:contactId`; this is an intentional correction.
PUT `/notifications/read-all` only affects the authenticated user's unread rows.
POST `/notifications` remains public for Post's internal calls.

Socket.IO uses the default namespace and `/socket.io/`, Engine.IO 4, polling,
WebSocket and upgrade. `join_user_room` accepts the existing scalar ID and joins
`user_<id>` without JWT authentication. Multiple sockets in the room receive the
same event. Clients explicitly rejoin after reconnect. Permissive socket CORS,
unauthenticated room joins, public in-app/email writes, local JWT validation and
synchronous email coupling remain documented security/availability debt.

A narrow ASGI adapter removes the optional queued Engine.IO NOOP text packet from
WebSocket upgrades, matching Node's namespace CONNECT order. It preserves polling
NOOP and all other control, application and binary frames. The actual Socket.IO
server still owns protocol parsing, heartbeat, room membership and events.

Email mock mode is active when `NODE_ENV != production`, `MOCK_EMAIL == true`, or
`SMTP_USER` is empty. Mock accepts missing recipient/subject. Real SMTP uses ordinary
SMTP with opportunistic STARTTLS when advertised, authentication, text/HTML bodies,
the existing sender display name, and a generated message ID. Real success is checked
against a local sink; STARTTLS sequencing is covered by unit tests. External delivery
is intentionally not attempted. Transport exceptions are exposed as a safe generic
500 message instead of leaking SMTP diagnostics. Finite dependency timeouts are also
an intentional operational improvement. Do not treat these tests as production SMTP
deliverability or multi-worker certification.

Logs contain request/dependency/event metadata only. Never enable Engine.IO debug
logging or print JWTs, OTPs, SMTP secrets, email/message bodies or resolved env files.
Foundation health, readiness and OpenAPI routes remain available on all Python services.

Phase 7 has not been performed. Review full integration/security debts and a deliberate
Node retirement/rollback policy before removing any legacy sources, images or schemas.
