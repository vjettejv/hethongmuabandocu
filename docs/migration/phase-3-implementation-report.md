# PHASE 3 IMPLEMENTATION REPORT

## 1. Summary

User và Category đã chuyển sang Django; canonical hybrid runtime hoạt động.
**335 local tests, 51 Phase 3 integration tests, 35 Phase 2 regression tests và real
E2E PASS. Phase 3 hoàn tất.** Không triển khai Phase 4.

## 2. Starting State

Branch develop, HEAD `92777b8f70b6717e3ffd12657c725b2ea4e3d0ab`.
Phase 1/2 chưa commit; .gitignore modified và Python/contracts/docs untracked.
HUONG_DAN_TRIEN_KHAI.md là pre-existing user work, giữ nguyên. Snapshot đầu Phase 3
gồm 411 files. Runtime đầu phase: Python Gateway/Auth healthy, tám business services
Node, tám DBs và frontend Nginx đang chạy. Không rebuild Gateway/Auth.

## 3. Final Hybrid Architecture

| Component | Runtime | Port |
|---|---|---|
| Gateway | FastAPI | 3000 |
| Auth | Django | 3001 |
| User | Django | 3002 |
| Post | Node | 3003 |
| Category | Django | 3004 |
| Message | Node | 3005 |
| Notification | Node, mock email | 3006 |
| Review | Node | 3007 |
| Search | Node | 3008 |
| Favorite | Node | 3009 |

Tám DB containers/volumes cũ và frontend giữ nguyên.

## 4. Gateway Route Matrix

| Public Route | Target | Rewrite | Runtime |
|---|---|---|---|
| /auth/* | auth-service:3001 | Strip /auth | Django |
| /users/* | user-service:3002 | Strip /users | Django |
| /posts/* | post-service:3003 | Strip /posts | Node |
| /categories/* | category-service:3004 | Strip /categories | Django |
| /messages/* | message-service:3005 | Strip /messages | Node |
| /notifications/* | notification-service:3006 | Strip /notifications | Node |
| /reviews/* | review-service:3007 | Strip /reviews | Node |
| /search/* | search-service:3008 | Strip /search | Node |
| /favorites/* | favorite-service:3009 | Strip /favorites | Node |
| /admin/posts/* | post-service:3003 | Original path | Node |
| /admin/categories/* | category-service:3004 | Original path | Django |
| /uploads/* | post-service:3003 | Original path | Node |
| /socket.io/* | message-service:3005 | Original path | Phase 2 compatibility proxy → Node |

Gateway source/config/image được giữ nguyên; canonical DNS đổi implementation.

## 5. User Architecture

profiles/models.py ánh xạ legacy table; selectors.py lookup theo authId;
authentication.py verify JWT locally và attach identity; services.py find-or-create/
partial updates; serializers.py projection và schema; views.py giữ envelopes;
urls.py đặt /me trước parameter; schema.py tài liệu no-trailing-slash paths.
Không default Django auth/session tables hoặc Auth HTTP lookup mỗi request.

## 6. User Database Mapping

UserProfile managed=False -> user_db.userprofiles. AutoField id là profile PK;
auth_id db_column=authId unique là logical Auth users.id, không ForeignKey.
full_name -> fullName; created_at/updated_at -> createdAt/updatedAt; phone/address/
avatar varchar255 nullable. Explicit UTC timestamps, numeric DB IDs; không ALTER.

## 7. User Endpoint Matrix

| Endpoint | Node | Django | Parity |
|---|---|---|---|
| GET /users/me | 200 profile; missing/error {} | Same for missing/DB lookup error | JWT + missing/profile contract tests |
| GET /users/{authId} | Public 200 profile; missing 404 error | Same normal/missing envelope | authId distinct from PK tested |
| PUT /users/me | Protected 200 find-or-create | Same; identity from JWT | Create/update/null/empty/partial/noop tested |
| PUT /users/{authId} | Public 200 find-or-create | Same public contract | Auth OTP dependency and parity tests |

Legacy creation quirks are preserved: unspecified optional fields are omitted from
the immediate create response, then appear null after DB lookup. URL PUT new profile
echoes authId decimal string, /me PUT uses numeric claim, later GET returns numeric.
Body id/authId/unknown fields do not override identity. External fields stay camelCase.

## 8. Auth→User Integration

Canonical Auth USER_SERVICE_URL already points to user-service:3002; no Auth code
change/direct user_db write. Real register→OTP→User profile→login→/users/me result:
PASS. Register→OTP tạo đúng profile, login/Python JWT→/users/me và partial update pass.
Notification remains Node mock, no real SMTP email.

## 9. Message→User Integration

Isolated original Node Message contact handler fetches Django User over real HTTP.
Synthetic message fixtures test successful fullName/username enrichment, camelCase
profile lookup, missing profile 404 and legacy `User <id>` fallback. Test-only preload
redirects the hardcoded canonical URL to user-candidate; Node source unchanged.
Result: PASS trong full 51-test live suite.

## 10. Category Architecture

categories/models.py unmanaged mapping; selectors.py unpaginated/no-order findAll;
services.py shared create/duplicate handling; serializers.py camelCase/time projection;
views.py separate normal/admin envelopes; urls.py root/admin/no-redirect compatibility;
schema.py canonical OpenAPI paths. App startup performs no sync/seed/DB mutation.

## 11. Category Database Mapping

Category managed=False -> category_db.categories; numeric AutoField id, name unique
varchar255 not null, description varchar255 nullable, createdAt/updatedAt DATETIME.
No new category table, migrations, FK or DB containers. Existing rows/IDs preserved.

## 12. Category Endpoint Matrix

| Endpoint | Node | Django | Parity |
|---|---|---|---|
| GET /categories | 200 raw Category[] | Same; no pagination/new ordering | Empty/existing list and timestamp comparison |
| POST /categories | 201 raw Category | Same | Create, missing/null name, duplicate, description variants |
| POST /admin/categories | 201 {data: Category} | Same | Separate envelope and error contract |

Missing/null name stays 500 `notNull Violation: Category.name cannot be null`;
duplicate stays 500 `Validation error`. Omitted description is stored null, omitted
from create response, then present as null on list; explicit null/empty are preserved.

## 13. Post→Category Integration

Original Node Post create/list/detail use Django Category over HTTP. Isolated create
uses multipart fields without uploaded files, schema-only Post tables and a Search
transport sink. Sink asserts create-time categoryName; list/detail assert enriched
Category fields. Real legacy Post list/detail are also read through Gateway in E2E.
No Post migration, legacy Post write or actual Search sync. Isolated create/list/detail
và canonical Post list/detail E2E: PASS.

## 14. Legacy Aliases

Gateway `/admin/categories` preserves path; `/categories/admin/categories` strips
generic prefix. Both reach Django admin create and retain {data: Category}. Root,
generic trailing slash and admin trailing slash are tested without 301/302 redirects.

## 15. Intentional Divergences

PARITY: missing /me 200 {}, public identity writes, find-or-create/partial/null/empty,
creation omissions/authId type quirks, camelCase, UTC milliseconds/Z, raw Category
array, normal/admin envelopes, common validation statuses/errors and legacy aliases.

INTENTIONAL BEHAVIOR CHANGE: no Category startup seed/sync; strict Bearer HS256 for
User aligned with Phase 2 Auth; malformed field types/noninteger identities return
controlled errors; unexpected DB exceptions return sanitized 500 instead of raw
legacy DB strings/status behavior. No full parity claim for every malformed input,
MySQL coercion case, race or failure. Schema-only Category Node reference disables
startup fixtures via test-only preload; actual list/create handlers remain unchanged.

## 16. Security Debt Deferred

Public GET/PUT /users/{authId}; public Category create/admin-create remain unchanged.
Migration does not add authorization. Existing Auth OTP/login/shared-key debt and
Node Post/Message/Search/Review issues remain documented in previous phases.

## 17. Tests

```powershell
.\.venv\Scripts\python.exe tools/verify_foundation.py
.\.venv\Scripts\python.exe -m pip check
$env:PHASE3_TEST='1'
.\.venv\Scripts\python.exe -u -m pytest integration-tests/phase3 -q
.\.venv\Scripts\python.exe tools/verify_phase3_runtime.py
```

Local: 335 tests = 40 Auth + 52 User + 34 Category + 96 other Django + 99 Gateway +
14 baseline contracts. **22/22 commands và 335 local tests PASS**.
**51 Phase 3 integration tests PASS in 146.74s**. Ruff/format (194 files), nine Django
checks và pip check PASS. Existing upstream Starlette/
httpx TestClient deprecation warning remains. Initial live failures exposed actual
Sequelize response omissions/authId typing and a URL-encoded test sent to the Post
multipart handler; fixed in Django compatibility/test transport, not by weakening
Node vs Django assertions or editing Node business source. Hai lỗi Unicode cuối là
MySQL CLI test connection charset; đặt SET NAMES utf8mb4, giữ assertion dữ liệu tiếng
Việt trong DB và GET, rerun 8 targeted cases rồi full 51-test suite thành công.

## 18. Phase 2 Regression

```powershell
$env:PHASE2_TEST='1'
.\.venv\Scripts\python.exe -u -m pytest integration-tests/phase2 -q
```

All original Auth/Gateway local tests remain in the runner. Live 35-test regression
including bcrypt/JWT, multipart/binary, headers, cookies, CORS, Nginx and Socket.IO:
**35/35 PASS in 127.81s**. Phase 2 source and baseline fixtures remain intact.

## 19. Docker Verification

Executed with runtime variables transiently taken from current baseline/Auth config;
không ghi credentials vào files mới/report hoặc commit. Exact overlay operations:

```powershell
docker compose -f docker-compose.yml -f docker-compose.phase2.yml -f docker-compose.phase3.yml config --quiet
docker compose --parallel 1 -f docker-compose.yml -f docker-compose.phase2.yml -f docker-compose.phase3.yml build user-service category-service
docker compose -f docker-compose.yml -f docker-compose.phase2.yml -f docker-compose.phase3.yml up -d --no-deps --wait --wait-timeout 90 user-service category-service
docker compose -f docker-compose.yml -f docker-compose.phase2.yml -f docker-compose.phase3.yml -f docker-compose.phase3.rollback.yml config --quiet
docker exec user-service python manage.py check
docker exec category-service python manage.py check
```

Build/config, User/Category container manage.py checks, health/readiness và cutover PASS.
Gateway/Auth/User/Category healthy; sáu Node services còn lại running. Rollback config
validated only, rollback not executed. Phase 3 uses separate Python image tags to
retain Node reference images and Phase 2 test reproducibility. No Gateway/Auth rebuild
or Node Post/Message recreation is required. Container ID/image/start timestamp đã
được đối chiếu: Gateway/Auth/Post/Message unchanged. Phase 1 prototypes retained.
Kết thúc: 19 runtime containers đang chạy; 14 opt-in test services đã stop.

## 20. Database Safety

Before snapshot: userprofiles 6 rows, categories 5 rows. Fingerprints include legacy
tables/columns/indexes/constraints. Real E2E cleanup và eight-DB compare PASS:

```text
user_db unexpected schema changes:
NONE

category_db unexpected schema changes:
NONE
```

User vẫn 6 rows, Category vẫn 5 rows; tám legacy schemas/row counts khớp snapshot
đầu Phase 3. Auto-increment có thể tăng vì synthetic writes; không reset.

Six explicitly owned schema-only Phase 3 clones exist in original User/Category/
Post/Message DB containers; no real rows copied, no new DB containers. Tests delete
only their owned clone fixtures. Real E2E guards profile slot before Auth OTP and
deletes only its UUID account/profile/category using IDs plus owned identities.
Never TRUNCATE/drop baseline/reset auto-increment. Snapshot compares schemas/counts,
not a checksum of all business values.
Sau full suites, tám tables trong sáu Phase 3 test schemas đã được kiểm tra empty;
schemas được giữ lại để tái lập tests, không drop hoặc reset auto-increment.

## 21. Files Created

36 files mới, đối chiếu snapshot trước phase:

```text
category-service/categories/exceptions.py
category-service/categories/models.py
category-service/categories/schema.py
category-service/categories/selectors.py
category-service/categories/serializers.py
category-service/categories/services.py
category-service/categories/urls.py
category-service/categories/views.py
category-service/tests/test_categories.py
contracts/categories/phase-3.json
contracts/users/phase-3.json
docker-compose.phase3.rollback.yml
docker-compose.phase3.test.yml
docker-compose.phase3.yml
docs/migration/phase-3-files.md
docs/migration/phase-3-implementation-report.md
docs/migration/phase-3.md
integration-tests/phase3/conftest.py
integration-tests/phase3/pytest.ini
integration-tests/phase3/test_category_parity.py
integration-tests/phase3/test_cross_service.py
integration-tests/phase3/test_user_parity.py
tools/prepare_phase3_tests.py
tools/runtime/phase3-reference-preload.cjs
tools/runtime/phase3-search-fixture.cjs
tools/verify_phase3_runtime.py
user-service/profiles/authentication.py
user-service/profiles/exceptions.py
user-service/profiles/models.py
user-service/profiles/schema.py
user-service/profiles/selectors.py
user-service/profiles/serializers.py
user-service/profiles/services.py
user-service/profiles/urls.py
user-service/profiles/views.py
user-service/tests/test_profiles.py
```

## 22. Files Modified

13 files được cập nhật:

```text
category-service/categories/apps.py
category-service/config/settings.py
category-service/config/urls.py
category-service/tests/test_health.py
contracts/README.md
docker-compose.python.yml
user-service/.env.example
user-service/config/settings.py
user-service/config/urls.py
user-service/profiles/apps.py
user-service/requirements.lock.txt
user-service/requirements.txt
user-service/tests/test_health.py
```

 Node source/package files/legacy Dockerfiles,
frontend, baseline Compose, seeds, Gateway/Auth business code and Phase 2 tests remain
unchanged. Phase 1 User additive Compose now receives required JWT env.

## 23. Git Status

PRE-EXISTING: HUONG_DAN_TRIEN_KHAI.md untracked and untouched.
PHASE 1: prior foundations, docs/contracts and .gitignore preserved; User/Category
foundations extended as listed in manifest.
PHASE 2: existing Gateway/Auth/proxy/parity implementations and evidence preserved.
PHASE 3: new/modified files distinguished using 411-file starting hash snapshot.
Branch/HEAD retained. No stage/commit/push/reset/cleanup command.

## 24. Known Issues

Public User/Category writes remain authorization debt. Real SMTP, browser-rendered
UI interactions and full Socket.IO delivery have not been certified. Phase 2 Nginx
DNS caveat remains if Gateway is recreated; Gateway is preserved in this cutover.
Legacy timestamps are second-precision in DB, millisecond-formatted externally.
No promise of atomic cross-service Auth/profile writes is introduced.

## 25. Phase 4 Readiness

Sẵn sàng cho Phase 4 — Post + Upload. Không còn blocker Phase 3: tests, runtime,
Auth→User, Node Message→User, Node Post→Category và DB safety đã pass. Authorization
debt/production caveats vẫn cần xử lý có chủ đích trong scope phù hợp. Chưa triển khai Phase 4.

## 26. Suggested Commits

Only suggestions; no commits created:

```text
feat(users): migrate user service to Django
feat(categories): migrate category service to Django
test(users): add Node Python profile parity tests
test(categories): add category contract and integration tests
test: add cross-runtime user and category regressions
docs: document phase 3 migration
```

Operational commands and lifecycle/rollback limits: [phase-3.md](phase-3.md).
Ignored local evidence lives in .artifacts/phase3; no JWT/password/OTP is in this report.

