# Phase 1 verification — 2026-10-06 (Asia/Saigon)

Status: **Phase 1 complete; Docker runtime verification PASS**.
After the user restored Docker, all final-source images were rebuilt and all ten
foundation containers passed health/readiness. The final DB snapshot comparison passed.
Docker engine: 29.8.2. No Phase 2 business implementation or traffic cutover is included.

## Baseline and preservation

- Branch: `develop`; HEAD: `92777b8f70b6717e3ffd12657c725b2ea4e3d0ab`.
- SHA-256 comparison of 157 pre-existing files: only `.gitignore` changed.
- Node sources, package files, Dockerfiles, frontend, Compose, seeds, import scripts,
  ignored legacy SQL backup and pre-existing `HUONG_DAN_TRIEN_KHAI.md` are unchanged.
- No commit or staging operation was performed.

## Results actually observed

| Command/check | Result | Evidence/limit |
|---|---|---|
| `python -m pip check` | PASS | No broken requirements |
| `ruff check .` | PASS | Python foundation scope |
| `ruff format --check .` | PASS | Python foundation scope |
| `python manage.py check` in each Django project | PASS | 9 projects, no issues |
| `python -m pytest -q` in each Django project | PASS | 16 each; 144 total; DB mocked |
| Gateway `python -m pytest -q` | PASS | 7 tests, 1 upstream deprecation warning |
| Contract `python -m pytest -q` | PASS | 14 tests; static inventory and comparator |
| `python tools/verify_foundation.py` | PASS | 22/22 commands; 165 tests total |
| Baseline `docker compose config --quiet` | PASS | Original Compose unchanged |
| Merged `docker compose ... config --quiet` | PASS | Additive Python overlay |
| Compare baseline/merged normalized service definitions | PASS | All 19 baseline definitions identical; 10 additions; no Python host ports/fixed names |
| Initial `docker compose ... build` for all 10 Python images | PASS | All images built before final logging/test refinements |
| Final-source image rebuild after recovery | PASS | All 10 rebuilt; Review rebuilt once more without cache to correct a missing appuser in its cached image |
| Start existing 8 MySQL containers and read-only metadata/counts | PASS | Original volumes reused; initial `SELECT 1` and snapshot succeeded |
| `docker compose ... up -d --no-deps` for 10 Python services | PASS | All 10 running and Docker healthy; only Python foundations started |
| `python tools/verify_runtime.py --http --compare ...` | PASS | 10 health + 10 ready HTTP 200; eight report database connected; request IDs and JSON headers correct |
| Final schema/row-count comparison after Python startup | PASS | All eight schema fingerprints and row counts match the original snapshot |
| Container `python manage.py check` | PASS | All nine Django services, Linux runtime |
| Peer DNS HTTP, OpenAPI and Swagger | PASS | Gateway container reaches all ten Python services; schema paths are health/ready only; docs HTTP 200 |

The exact aggregate local command was:

```powershell
.\.venv\Scripts\python.exe tools/verify_foundation.py
```

Tests exercise public health, ready success/503 with mocked connections, request IDs,
CORS allow/reject, JSON logging without secret message text, OpenAPI limited to health
and ready, no business routes/models, and the legacy contract inventory. They neither
create a test database nor run migrations. These are foundation tests, not migrated
business parity tests.

## Docker failure and recovery attempts

The first build completed all ten images. A later parallel rebuild encountered a
BuildKit missing-parent snapshot error. Sequential rebuilding succeeded for eight
final-source images, then the engine disconnected with `rpc ... EOF` on Search.
Docker VM logs recorded `dockerd` fatal signal 7 and subsequently
`fork/exec /usr/local/bin/dockerd: input/output error`.

Docker API requests returned HTTP 500 or a missing engine pipe. Desktop stayed in
`starting`. Recovery attempts used Desktop restart/stop with bounded retries,
termination of only the `docker-desktop` WSL distro, and restart of verified Docker
executables. No Docker reset, prune, container deletion, volume deletion, VHD deletion
or legacy schema operation was performed. This was an environment failure rather
than a confirmed Python application issue.

The user subsequently restored Docker. Sequential rebuilding completed all ten
images. The first startup then exposed a Review cached image without its declared
appuser. A read-only image probe confirmed the missing account. A Review-only
`build --no-cache` corrected it; UID 10001 was verified and the container started.
No source-code workaround or cache/volume deletion was used. All ten Docker
healthchecks are now healthy. Runtime health, readiness, peer DNS, OpenAPI, Swagger,
container Django checks and the original DB snapshot comparison all passed.

Reproduction commands remain in [phase-1.md](phase-1.md). Preserve the Compose
project/volumes and the original snapshot. Phase 2 preparation is in
[phase-2-readiness.md](phase-2-readiness.md).

## Database snapshot taken before Python startup

| DB | Tables and row counts |
|---|---|
| auth_db | users: 244 |
| user_db | userprofiles: 6 |
| post_db | posts: 4463; images: 35 |
| category_db | categories: 5 |
| message_db | messages: 31; notifications: 2 |
| review_db | reviews: 4 |
| search_db | searchindices: 4872 |
| favorite_db | favorites: 3 |

Schema fingerprints cover columns, indexes, constraints, FK rules and case mode.
Row counts are not hashes of every stored business value. No Django system tables
were present. MySQL case mode was 1; Review's live table contained `imageUrl`.

```text
Legacy schema changes performed:
NONE
```

The original snapshot matched both before recovered Python startup and after all
ten foundations were running. No legacy schema changes were performed.

## Local evidence and scope limitations

Ignored, local evidence: `.artifacts/phase1/final-local-checks.log`, `db-before.json`,
`docker-start.log`, `runtime-checks.log` retain the original failure evidence.
Recovery evidence: `docker-final-build.log`, `docker-review-rebuild.log`,
`docker-recovery-start.log`, `db-recovery-check.log`, `runtime-recovery-checks.log`,
`container-django-checks.log` and `peer-network-checks.log`. The dependency environment
is Python 3.12.14.
Starlette's TestClient emits one upstream warning about the httpx integration; the
gateway tests pass. No additional client dependency was added just to suppress it.
No Node business containers were started because their startup can run Sequelize
schema synchronization. Concurrent Node/Python business parity is not claimed.
