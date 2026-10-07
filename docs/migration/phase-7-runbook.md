# Phase 7 canonical Python operation

The root `docker-compose.yml` is the ordinary Python entry point after consolidation.
FastAPI Gateway 3000 forwards to Django services 3001–3009; Message runs Socket.IO in
one Uvicorn worker and Notification is DB-less. Frontend/Nginx stays unchanged on :80.

Copy `.env.example` to ignored `.env` and supply existing deployment values privately.
Existing keys/passwords are preserved; do not rotate them as a startup shortcut. Phase 7
created a private local `.env` from running container settings when no user file existed.
Do not print resolved Compose or container environment. SMTP defaults to mock mode;
external deliverability is environment-dependent and was not tested.

The nine named data/upload volumes use their original `kientrucpm_*` names and are
external. They must already exist; this is a migration of an existing deployment.
The network is `kientrucpm_do-cu-micro-net`. Preserve internal-only Message/Notification
ports and current DB port mappings. Post/Review preserve the shared uploads mount and
its current permissions. No business table migrations run at startup.

```powershell
docker compose config --quiet
docker compose up -d --build
.\.venv\Scripts\python.exe tools/verify_phase7_state.py --runtime
docker compose down
```

`down` stops processes/network while retaining the external data volumes. Do not use
`down -v`, `volume rm`, table truncation, schema drop or ID-counter resets.

Normal verification needs Python services only. Node is used solely for the unchanged
frontend build and its actual Socket.IO client compatibility harness:

```powershell
.\.venv\Scripts\python.exe tools/verify_foundation.py
.\.venv\Scripts\python.exe -m pip check
powershell -NoProfile -ExecutionPolicy Bypass -File tools/verify_phase7_integration.ps1 -Canonical
.\.venv\Scripts\python.exe tools/verify_phase7_state.py --preservation --runtime --files
.\.venv\Scripts\python.exe tools/audit_phase5_search.py --compare .artifacts/phase7/search-drift-before.json
```

The Phase 7 E2E requires the recorded baseline in `.artifacts/phase7`, an empty owned
Search shadow schema, and `MOCK_EMAIL=true`. It uses Nginx for business HTTP and actual
Socket.IO polling/WebSocket/upgrade delivery. It registers `.invalid` accounts and uses
their real JWTs; creates one Post image and one Review image; exercises moderation,
Search, Favorite, Review, Message and notifications; then removes only journal-owned
synthetic records/files. Post owner-delete intentionally keeps physical uploads, so the
test explicitly removes its own file by UUID name and byte hash. Search changes only
to its owned shadow during E2E and is restored in `finally` to protect old orphan IDs.

If interrupted, inspect `.artifacts/phase7/runtime-owned.json` privately. Confirm exact
UUID/IDs and account ownership before cleanup. Never delete unknown rows or uploads.
Baseline schema/count/full-content hashes and 46 upload entries must compare equal after
cleanup. Search's 409 pre-existing orphans and mismatches remain unreconciled.

For later verification after legitimate application writes, capture a fresh baseline
in a new ignored directory; never overwrite the original Phase 7 evidence:

```powershell
$baseline = ".artifacts/check-" + [guid]::NewGuid().ToString('N')
.\.venv\Scripts\python.exe tools/snapshot_phase7_state.py --directory $baseline
.\.venv\Scripts\python.exe tools/audit_phase5_search.py --output "$baseline/search-before.json"
powershell -NoProfile -ExecutionPolicy Bypass -File tools/verify_phase7_integration.ps1 -Canonical
.\.venv\Scripts\python.exe tools/verify_phase7_state.py --directory $baseline --preservation --runtime
.\.venv\Scripts\python.exe tools/audit_phase5_search.py --compare "$baseline/search-before.json"
```

Historical parity tests are opt-in and use immutable Git source/cache plus isolated
schemas. They are not dependencies of the normal commands above. See
`phase-7-rollback.md` for recovery and `phase-7-node-retirement-manifest.md` for removals.
The wrapper recreates only disposable fixtures so their network IDs stay valid after
a canonical cold restart. Existing isolated test schemas/images must be prepared using
the corresponding `tools/prepare_phase2_tests.py` through `prepare_phase6_tests.py`
workflow; immutable reference exports are regenerated automatically. Select one suite:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/verify_phase6_regressions.ps1 -Phase 2
# The same wrapper accepts -Phase 3, 4, 5 or 6.
```

These suites intentionally boot reference Node processes, stop them in `finally`, and
leave their disposable containers/images available for subsequent opted-in runs. They
are excluded from ordinary root Compose startup. Retired source is read from immutable
Git objects or the ignored export cache, never from active backend entrypoints.
Phase 1–6 reports/contracts remain historical evidence. Their old cumulative runtime
startup examples do not supersede the canonical command here.

Known debts stay scoped out: public room joins/internal writes, permissive socket CORS,
shared JWT quality, moderation/review authorization, synchronous best-effort email,
Post's bounded asynchronous side effects, process-local rooms without replay, existing
Search drift and production SMTP verification. No Redis/multi-worker redesign or CI/CD
is introduced. Phase 8 is not executed here.
