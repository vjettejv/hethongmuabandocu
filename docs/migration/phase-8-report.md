# Phase 8 implementation report

Date: 2026-10-07. All secret values withheld.

## 1. Summary

Configured GitHub Actions CI and a gated GHCR build/publish workflow; replaced the current README and added architecture/API/development/CI-CD guides. Added schema-only fresh-volume bootstrap and a portable isolated integration runner. Business APIs, existing database schemas/content, credentials, and upload files are preserved. No staging, commit, push, tag, publication, or deployment was performed.

Final gate status is recorded below; historical Phase 7 metrics are not counted as new Phase 8 execution.

## 2. Starting State

Branch `develop`, HEAD `92777b8f70b6717e3ffd12657c725b2ea4e3d0ab`; remote `vjettejv/hethongmuabandocu`. Both `develop` and `main` existed when workflow triggers were chosen. The repository already had extensive uncommitted migration/frontend/moderation work. Those changes were retained.

Phase 7 historically recorded 913 PASS, 48 full-system cases, two cold starts, eight databases, and 46 uploads. Later authorized changes mean the fresh Phase 8 baseline has **47 uploads**, Post 4464 rows (4442 pending / 22 approved), and Search 4872 rows (4850 pending / 22 approved). The Phase 8 file delta is computed against the pre-edit file hashes, not Git HEAD; prior removals are not attributed to this phase.

## 3. Final Architecture

FastAPI/HTTPX Gateway + nine Django/DRF services; Python ASGI/python-socketio Message with one worker; database-free Notification; eight MySQL databases; React/Vite compiled into Nginx; shared Post/Review uploads. Root Compose: **19 containers = 10 backend + 8 database + 1 frontend**, with nine external persistent volumes. No canonical Node backend runtime.

## 4. CI Workflow

`.github/workflows/ci.yml`: pull requests, pushes to existing `develop`/`main`, manual dispatch, reusable calls; Ubuntu 24.04; Python 3.12; Node 18. Three jobs: Python quality, frontend, Docker integration. `contents: read`; pinned action SHAs; locked dependencies; job timeouts and cancellation. Python checkout fetches full Git history for the recorded contract oracle (`git show`); the old Node source is not executed. PR smoke selects 11 cases; other triggers select all 48. Only non-sensitive JUnit/result artifacts are uploaded.

## 5. CI Commands

```bash
python -m pip install -r requirements-dev.lock.txt
python -m pip check
python tools/verify_foundation.py
npm ci --prefix do-cu-frontend
node do-cu-frontend/tests/frontend-contracts.test.js
npm run build --prefix do-cu-frontend
python tools/verify_ci.py --validate-only
python tools/verify_ci.py --smoke
python tools/verify_ci.py
```

Foundation executes Ruff lint/format, all nine Django checks, an explicit gateway import, service/gateway tests, and contract/tooling tests. The portable CI runner creates random credentials and UUID-only containers/network/images/volumes, uses schema-only SQL plus synthetic fixtures, removes canonical port/volume bindings, and cleans only resources it owns. MySQL buffer/redo limits apply only to disposable CI databases. No developer `.env` or private user seed rows are imported.

## 6. CI Local Verification

Windows foundation: **23/23 commands PASS, 521 tests PASS**, local Python 3.13; the exact final source was also checked on Linux Python 3.12. Frontend host checks use Node 24; Docker and configured GitHub jobs use the existing Node 18 toolchain. Actionlint 1.7.12: both workflows PASS; official release binary verified against the upstream SHA-256 checksum. Shellcheck/Pyflakes integrations were disabled for this local Windows actionlint invocation.

Final Linux Python 3.12 verification: **23/23 commands, 521 cases PASS**, exact dev lock installation and pip check PASS. Isolated full: **48 PASS in 188.41 s**; isolated smoke: **11 PASS in 52.73 s**; both owned cleanup PASS. Local runs do not establish a successful remote GitHub workflow. The first two isolated runs built/started nineteen healthy containers but failed when Docker Desktop stopped with **disk full**; they are not PASS and are not included in successful test totals. Their UUID containers/volumes were subsequently cleaned without touching canonical external volumes. Further clean-install attempts exposed missing database readiness and the historical Review seed missing `imageUrl`. Added TCP `SELECT 1` readiness to all eight databases, HTTP readiness to frontend, and generated all eight schema-only templates from the actual preserved DDL using read-only `SHOW CREATE TABLE`. TCP probes and schema-only initialization were rerun successfully. No failed business assertion was weakened.

## 7. CD Workflow

`.github/workflows/docker-publish.yml`: valid `vMAJOR.MINOR.PATCH[-prerelease]` tag publication; manual dispatch defaults `publish=false`; explicit manual publication restricted to main/develop or a valid version tag. Reusable CI validation precedes the image matrix. GHCR uses the built-in `GITHUB_TOKEN`, with `packages: write` only on the image job. No PAT or secret literal is embedded. Buildx cache scopes are per service; image matrix parallelism is three.

## 8. Docker Image Matrix

Eleven images, each `ghcr.io/vjettejv/hethongmuabandocu-<service>`: api-gateway, auth-service, user-service, post-service, category-service, message-service, notification-service, review-service, search-service, favorite-service, frontend. Backend contexts match their service directories; frontend uses `do-cu-frontend`. Exact version reference and `sha-<full SHA>` tags; `latest` only on stable version tags, not prereleases/branch dispatches. Full matrix/context details: [CI/CD guide](../ci-cd.md).

## 9. Publish Status

**NOT PERFORMED.** No local login/push, Git tag, release, GitHub workflow dispatch, or production deployment. Workflow YAML is configured and locally validated; remote credentials/package permission behavior still requires an authorized future remote run.

## 10. README

Rewritten in professional English with current architecture, the full service/framework/port/database matrix, nineteen-container explanation, clean startup/shutdown, environment guidance, tests, CI/CD, Socket.IO/one-worker behavior, migration history, repository map, and concrete limitations. Removed misleading current Node backend instructions. Historical user guide remains byte-identical.

## 11. Architecture Docs

Created `docs/architecture.md`, `docs/api.md`, `docs/development.md`, and `docs/ci-cd.md`; added a migration evidence index. Documents external identifiers, unmanaged tables, ownership, request paths, shared file retention, MySQL Search projection/drift, current event names (`join_user_room`, `receive_message`, `receive_notification`), HTTP message writes, and legacy authorization boundaries. Updated the existing Vietnamese project/CV overview to describe CI configuration without claiming publication or production deployment.

## 12. Developer Workflow

New developer: copy `.env.example`, fill private keys/passwords, create only missing external volumes with `bootstrap_volumes.py`, validate quiet Compose, build/start root stack, inspect health, open localhost/docs, stop with ordinary `down`. Eight schema-only templates initialize empty volumes without historical accounts. Existing volumes retain their data and credentials. Fresh business tables are empty; no private fixture SQL or previous phase run is required.

Frontend README now describes the real scripts. Added the missing `/favorites` prefix to Vite's development proxy; its routing probe and build PASS. No business client/API behavior changed. Python/macOS/Linux/PowerShell setup and historical opt-in test boundaries are documented.

## 13. Repository Cleanup

Minimal: removed the dead root `x-node-guard` extension; renamed eight remaining phase-labeled canonical Python image names; switched all eight fresh initialization binds to schema-only inputs matching current DDL; added eight database and one frontend healthcheck; excluded private frontend `.env*` from Docker context. No source file was removed by Phase 8. Old SQL seeds, recovery/parity tooling, Phase 0–7 reports, and stopped historical Docker fixtures remain as evidence. Generated caches/logs/SQL/test configs stay ignored under `.artifacts/` or existing ignore rules; no broad Docker/filesystem prune was performed.

## 14. Dependency/Environment Audit

Python dev lock and per-image requirements were preserved; frontend package-lock preserved. Required canonical secret variables have no literal fallback in root Compose. `NODE_ENV` is retained for compatibility, not a backend Node process. Existing `.env` is ignored and untouched; no credential rotation. `.env.example` distinguishes new installation from existing deployment. Docker contexts exclude private environment files.

`npm audit`: **17 advisories (1 low, 7 moderate, 9 high, 0 critical)** in the existing lock. Direct affected packages include axios, react-router-dom, and Vite. No forced dependency upgrade/lockfile rewrite was made in this migration/documentation phase. Node 18 remains current project tooling and is a separate upgrade debt.

## 15. Secret Scan

Read-only intended-file scan and Python AST/root Compose audit PASS: no literal canonical runtime signing/database/SMTP secrets; no matched private-key/provider-token patterns; private environment paths ignored. Seven historical SQL seed files containing account/profile rows were reviewed, preserved, and excluded from canonical/CI initialization. Values were not included in audit output. This is a scoped pattern/assignment scan, not entropy analysis or a remote Git-history secret audit. Evidence: ignored `.artifacts/phase8/source-audit.json` and `secret-scan.json`. Protected guide, `.gitignore`, and existing migration reports remain byte-identical.

## 16. Ruff

`python -m ruff check .` PASS; `python -m ruff format --check .` PASS. Canonical source uses Python 3.12 lint target. New Python tooling is formatted; no global formatting of historical docs/user files.

## 17. Django Checks

All nine `manage.py check` commands PASS in Windows foundation; Linux checks also PASS on the final source snapshot. Checks use synthetic settings/blocked database endpoints and do not apply migrations or write legacy tables. Gateway import is explicitly checked.

## 18. pip check

Windows virtual environment PASS (`No broken requirements found`). Linux container installs the exact root development lock; its pip consistency check PASS (`No broken requirements found`). No global host Python package installation or lock upgrade.

## 19. Frontend Build

`npm ci`, eleven frontend contract cases, Vite production build, and the Favorite development-proxy routing probe PASS. Root/CI image builds also build frontend with Node 18. The host used Node 24; that distinction is retained instead of claiming the host executed Node 18. Bundle generation does not prove production browser deployment.

## 20. Tests

| Selection | Unique cases | Local result |
|---|---:|---|
| Auth unit | 40 | PASS |
| User unit | 52 | PASS |
| Post unit | 84 | PASS |
| Category unit | 34 | PASS |
| Message unit | 47 | PASS |
| Notification unit | 35 | PASS |
| Review unit | 44 | PASS |
| Search unit | 25 | PASS |
| Favorite unit | 33 | PASS |
| Gateway unit | 99 | PASS |
| Contract/tooling | 28 | PASS |
| Foundation subtotal | **521** | PASS |
| Canonical full-system | **48** | PASS on existing stack and clean isolated stack |
| Frontend contracts | **11** | PASS |

**580 unique current cases PASS** = 521 + 48 + 11. Linux reruns, isolated reruns, smoke subsets, lint, health/system-check commands, and builds are not added as new cases. Fourteen Phase 8 tooling cases are already included in contract 28/foundation 521. Phase 7's historical 913 is not added to this total.

## 21. Docker Config/Build

Canonical and isolated `config --quiet` PASS. Eleven image builds PASS during root cold start and isolated startup. Python image entrypoints/DB names/shared mounts are verified; no canonical Node process. Build caches are permitted; this is not a claim of eleven `--no-cache` builds.

## 22. Cold Start

Ordinary canonical `docker compose down` followed by `docker compose up -d --build --wait --wait-timeout 240` PASS after minimal cleanup: nineteen healthy containers. No volume deletion or orphan removal on the canonical project. Final ordinary root rebuild/start also PASS after isolated testing: **19/19 Docker healthchecks healthy**, all ten Python backends ready, frontend serving. Stack is left running at localhost. Interrupted disk-full CI starts are not counted as successful cold starts.

## 23. Socket.IO Regression

Existing canonical 48-case suite PASS (170.27 seconds), with real Socket.IO 4.x client: polling, direct WebSocket, polling-to-WebSocket upgrade, room join, HTTP message persistence/receive event, notification persistence/receive event, offline/reconnect/history/privacy paths, and journal-owned cleanup. Message remains one Uvicorn worker. Full checks are in ignored `.artifacts/phase8/canonical-e2e/e2e-checks.json`; tests were not replaced with mocks.

## 24. Database Safety

| Database | Preserved table counts |
|---|---|
| auth_db | users=244 |
| user_db | userprofiles=6 |
| post_db | images=36, posts=4464 |
| category_db | categories=5 |
| message_db | messages=34, notifications=2 |
| review_db | reviews=4 |
| search_db | searchindices=4872 |
| favorite_db | favorites=3 |

All eight schema fingerprints, counts, and full-row content hashes equal the fresh Phase 8 baseline after canonical E2E. Test rows were journal-owned and cleaned. No business migration, reset, bulk repair, or old status restoration. Fresh schema templates are initialization for empty new volumes only. Final restored-stack comparison also PASS; evidence `.artifacts/phase8/safety-final.log`. All eight schemas, all table counts, and all full-row hashes match the same pre-edit runtime baseline.

## 25. Upload Safety

**47 original files preserved**: identical paths, byte lengths, and SHA-256 values after canonical E2E. Temporary test image files were verified as UUID-owned and removed. Existing shared volume name/path/permissions retained. No original upload directory reset or migration.

## 26. Search Drift

Read-only before/after comparison PASS: Search 4872 rows, Post 4464, 408 orphan rows, 4464 matched rows, zero approved posts missing; mismatch counts title=11, description=11, price=11, categoryId=8, status=0, imageUrl=10, categoryName=11; one ambiguous image row. Projection content SHA-256 `206ca8f45be4958e204d558c6e7704de55eb58cede9e32969f75f9eabd2951b9` unchanged. Tests temporarily used an owned empty shadow schema and restored canonical Search. No real projection rebuild or drift repair.

## 27. Files Created

- `.github/workflows/ci.yml`
- `.github/workflows/docker-publish.yml`
- `contract-tests/test_final_tooling.py`
- `docs/api.md`
- `docs/architecture.md`
- `docs/ci-cd.md`
- `docs/development.md`
- `docs/migration/README.md`
- `docs/migration/phase-8-report.md`
- `seeds/schema/auth.sql`
- `seeds/schema/category.sql`
- `seeds/schema/favorite.sql`
- `seeds/schema/message.sql`
- `seeds/schema/post.sql`
- `seeds/schema/review.sql`
- `seeds/schema/search.sql`
- `seeds/schema/user.sql`
- `tools/bootstrap_volumes.py`
- `tools/verify_ci.py`

## 28. Files Modified

- `.env.example`
- `README.md`
- `do-cu-frontend/.dockerignore`
- `do-cu-frontend/README.md`
- `do-cu-frontend/vite.config.js`
- `docker-compose.yml`
- `docs/project-overview.md`
- `integration-tests/phase7/test_full_system.py`
- `tools/verify_foundation.py`
- `tools/verify_phase6_runtime.py`
- `tools/verify_runtime.py`

## 29. Files Removed

**None in Phase 8.** Earlier Phase 7's 125 retired paths and other pre-existing dirty changes are not counted as this phase. Generated UUID-owned CI Docker resources were removed; canonical volumes and historical fixtures were not pruned.

## 30. Git Status

All changes remain uncommitted/unstaged on the original branch. `git diff --cached --name-only` is empty; HEAD unchanged. Full local status saved privately in `.artifacts/phase8/git-status-final.txt`. Phase 8 file lists above are the delta against `.artifacts/phase8/baseline/before-filehashes.json`, so they distinguish prior user work from this phase.

## 31. Known Remaining Debt

Legacy OTP/JWT/access-control boundaries, unauthenticated Socket.IO room identity, single-worker room state, best-effort MySQL Search projection with existing drift, shared-file retention/orphan behavior, SMTP mock by default, existing frontend dependency advisories/Node toolchain, and deployment hardening/monitoring/backups. No production scale/performance/security claims. Disk capacity can stop Docker and invalidate a run; adequate free space is a developer prerequisite. Remote GitHub/GHCR execution remains unperformed.

## 32. Proposed Commit Plan

Proposal only, never staged/executed:

1. Review and commit the previously authorized Phase 1–7 Python migration/retirement as separate logical groups using their existing reports.
2. Review the pre-existing frontend/session/footer and moderation normalization work separately.
3. Commit Phase 8 CI/GHCR workflows, portable test runner, test targeting, and tooling contracts.
4. Commit schema-only clean bootstrap, canonical image/Compose cleanup, environment example, and frontend context/dev proxy corrections.
5. Commit current README, architecture/API/development/CI-CD guides, CV overview, evidence index, and this report.

Preserve the user-authored guide and all historical reports. Include no `.env`, generated artifacts, user dumps, dependency caches, or private logs. Future push/tag/publication requires its own authorized repository release action.

## 33. Final Run Commands

```bash
# First clone: copy/fill .env privately, then create only missing volumes.
python tools/bootstrap_volumes.py --create-missing
docker compose config --quiet
docker compose up -d --build
docker compose ps

# Activated Python environment with the committed development lock installed.
python tools/verify_foundation.py
python -m pip check
python -m ruff check .
python -m ruff format --check .
node do-cu-frontend/tests/frontend-contracts.test.js
npm run build --prefix do-cu-frontend

# Isolated final canonical integration; no private fixture data needed.
python tools/verify_ci.py --smoke
python tools/verify_ci.py

# Stop the canonical development stack without deleting volumes.
docker compose down
```

`verify_ci.py` wraps the actual `python -m pytest -c integration-tests/phase7/pytest.ini integration-tests/phase7 -q` invocation with generated target environment and owned setup/cleanup. Do not run that raw pytest command against an unprepared real stack.

## 34. Final Project Status

All required local gates PASS. Canonical stack is running at localhost with 19 healthy containers. CI/CD means configured workflows, not remote execution.

| Final gate | Result |
|---|---|
| Ruff lint/format; actionlint | PASS |
| Windows + Linux Python foundation | 23/23 commands and 521 cases PASS on each platform |
| Nine Django checks; gateway import; pip check | PASS |
| Frontend install/contracts/build; Favorite dev proxy | PASS (11 contract cases) |
| Isolated CI smoke / full | 11 / 48 PASS, owned cleanup PASS |
| Canonical 48-case regression including real Socket.IO | PASS |
| Final root Compose build/start/health | PASS (19/19 healthy) |
| Eight DB schemas/counts/full-row hashes | Preserved |
| 47 original uploads | Identical bytes/hashes |
| Search content/drift | Unchanged |
| Guide/gitignore/historical reports; Git index/HEAD | Preserved; no staging/commit |
| Remote GitHub Actions / GHCR publication / production deploy | NOT PERFORMED |

```text
MIGRATION STATUS:
COMPLETE

CANONICAL BACKEND:
PYTHON

NODE BACKEND RUNTIME:
NONE

CI/CD:
CONFIGURED

PRODUCTION DEPLOYMENT:
NOT PERFORMED
```

Final verified developer commands (activated environment and private `.env` prepared as documented):

```bash
docker compose up -d --build
docker compose ps
python tools/verify_foundation.py
python tools/verify_ci.py
python -m ruff check .
python -m ruff format --check .
python -m pip check
docker compose down
```
