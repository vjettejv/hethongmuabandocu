# Phase 3: Django User + Category

Canonical `user-service:3002` and `category-service:3004` now run Django. Gateway/Auth
keep their verified Phase 2 images. Post/Message/Notification/Review/Search/Favorite
remain Node. Eight original DB containers/volumes are reused without migrations.
No frontend or Node business source change is needed. No Phase 4 APIs are implemented.

## Cutover

Use the existing project `kientrucpm` and the shared JWT/DB credentials documented
in Phase 2. `.env.python` is ignored; the committed example contains placeholders.
Keep the same shared JWT key. Phase 3 adds no new secret or service host port.

```powershell
docker compose --env-file .env.python -f docker-compose.yml -f docker-compose.phase2.yml -f docker-compose.phase3.yml config --quiet
.\.venv\Scripts\python.exe tools/verify_runtime.py --snapshot .artifacts/phase3/db-before.json
docker compose --env-file .env.python --parallel 1 -f docker-compose.yml -f docker-compose.phase2.yml -f docker-compose.phase3.yml build user-service category-service
docker compose --env-file .env.python -f docker-compose.yml -f docker-compose.phase2.yml -f docker-compose.phase3.yml up -d --no-deps user-service category-service
```

Only User/Category are recreated. Gateway routing already uses their canonical DNS,
so its prefixes/admin path rewrites and streaming/Socket.IO proxy remain unchanged.
Auth and Node Message use `user-service:3002`; Node Post uses `category-service:3004`.
The overlay clears Node preloads/source mounts for the two Python containers.
Legacy Node images/source remain available. Do not run baseline Sequelize startup
unguarded against legacy DBs. Never run migrations, imports or `down -v` for cutover.
If Gateway is recreated independently, follow Phase 2's frontend restart instruction.

## API and lifecycle

User maps `user_db.userprofiles` with `managed=False`. Numeric profile `id` and
logical Auth `authId` are distinct. `/me` is ordered before the parameter route,
verifies JWT locally, and uses claims.id. GET missing `/me` remains `200 {}`;
public GET missing `/{authId}` remains `404 {error: "Profile not found"}`.
PUT uses find-or-create, permits only fullName/phone/address/avatar, ignores body
identity, preserves omitted fields, and writes explicit null/empty strings.
No-op updates preserve updatedAt. On creation, omitted optional fields are absent
from the immediate response, but become null in a later GET. URL PUT create echoes
the decimal authId string; `/me` PUT and DB reads return numeric authId, as Node does.
Public PUT `/{authId}` remains deferred security debt.

Category maps `category_db.categories`, unique name and numeric auto-increment ID.
GET `/` is a raw array without pagination/new ordering. POST `/` returns raw Category;
POST `/admin/categories` returns `{data: Category}`. Both public gateway admin forms
work, including `/categories/admin/categories`. Missing name and duplicate errors
retain legacy status/envelope. Omitted description is stored null but omitted from
the create response, and appears as null on list reload; explicit null/empty is preserved.
Trailing-slash forms are accepted directly without redirects. API timestamps use
UTC ISO milliseconds/Z; persisted legacy DATETIME retains second precision.

Parity is separate from intentional changes: Django does not seed on startup, so
an empty Category DB remains empty. Unexpected DB errors never expose SQL/credentials.
Malformed identities/field types use controlled errors. User accepts only Bearer HS256
as Phase 2 Auth does, while legacy User accepted other header schemes/HS algorithms.
Public profile writes and Category/admin creates remain authorization debt.
Gateway owns browser CORS; internal services default to no browser origins.

## Reproducible verification

```powershell
.\.venv\Scripts\python.exe tools/verify_foundation.py
.\.venv\Scripts\python.exe tools/prepare_phase2_tests.py
.\.venv\Scripts\python.exe tools/prepare_phase3_tests.py
docker compose --env-file .env.python -f docker-compose.yml -f docker-compose.phase2.yml -f docker-compose.phase3.yml -f docker-compose.phase2.test.yml -f docker-compose.phase3.test.yml --profile phase2-test --profile phase3-test up -d --no-deps auth-reference auth-candidate user-test notification-test proxy-fixture gateway-probe user-reference user-candidate category-reference category-candidate message-cross post-cross phase3-search-fixture gateway-phase3-probe
$env:PHASE3_TEST='1'
.\.venv\Scripts\python.exe -m pytest integration-tests/phase3 -q
$env:PHASE2_TEST='1'
.\.venv\Scripts\python.exe -m pytest integration-tests/phase2 -q
.\.venv\Scripts\python.exe tools/verify_phase3_runtime.py
.\.venv\Scripts\python.exe tools/verify_runtime.py --compare .artifacts/phase3/db-before.json
```

Test schemas are explicitly owned empty clones in existing DB containers:
phase3_user_node/python, phase3_category_node/python, phase3_post_test, phase3_message_test.
Setup refuses a pre-existing unowned schema. No real account or business row is copied.
Fixtures DELETE only within owned schemas, never TRUNCATE/reset auto-increment.
Node reference source/server are mounted read-only with the existing schema guard.
The test-only preload suppresses Category's startup seed and routes the hardcoded
Message User URL to `user-candidate`. Business handlers remain unchanged. Search
writes from isolated Node Post creation go to a test transport sink that records
only synthetic postId/categoryId/categoryName, never legacy Search. Ports are random
loopback-only. Explicitly build Node reference
services if their retained tags are absent. Tests establish Message contact success/
404 fallback and Post create/list/detail category consumption without migrating them.

The real E2E verifier creates a UUID synthetic Auth account, refuses an occupied
profile slot, verifies OTP creates the Django User profile, logs in, verifies JWT
and reads/updates `/me`. It creates one owned Category through Gateway, reads actual
Node Post list/detail enrichment, then deletes only the owned identity/ID records.
No real email is sent. Schema/count comparison covers all eight DBs; it does not
checksum every business value. Stop only the opt-in test services after checking.

## Rollback

`docker-compose.phase3.rollback.yml` is an optional LAST overlay after baseline,
Phase 2 and Phase 3. It restores only Node User/Category with the schema guard and
retains Python Gateway/Auth. Configuration validation does not certify executed
rollback. Node Category's original empty-DB startup seed returns on rollback.
Use the same project/env/volumes; apply only deliberately. To restore Django, remove
that last overlay and start User/Category with the normal Phase 3 files.

Phase 4 is Post + Upload. This phase only tests existing Node Post behavior.
