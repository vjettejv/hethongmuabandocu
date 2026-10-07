# Phase 5: Django Favorite, Review and Search

Gateway/Auth/User/Post/Category/Favorite/Review/Search run Python. Only Message
and Notification remain Node. No Phase 6 work, frontend changes, message broker,
cloud uploads or Elasticsearch is introduced.

## Normal runtime and rollback

Use the existing Compose project `kientrucpm`, ignored `.env.python` and shared
secrets from Phase 2–4. Never dump resolved Compose environments or inspect Env
arrays into logs. Apply the overlays in order:

```powershell
$phase5Stack = @('-f','docker-compose.yml','-f','docker-compose.phase2.yml','-f','docker-compose.phase3.yml','-f','docker-compose.phase4.yml','-f','docker-compose.phase5.yml')
docker compose --env-file .env.python @phase5Stack config --quiet
docker compose --env-file .env.python @phase5Stack build favorite-service review-service search-service
docker compose --env-file .env.python @phase5Stack up -d --no-deps favorite-service review-service search-service
```

Canonical DNS/ports remain favorite-service:3009, review-service:3007 and
search-service:3008. Gateway source/image is unchanged. Review reuses the exact
original `kientrucpm_shared_uploads:/app/uploads` RW mount with Post. Only Review
uses the legacy root identity for its existing root-owned volume; no chmod/chown,
rename, whole-volume cleanup, replacement table or DB migration runs at startup.
Favorite/Search use the Python image's appuser. Health never accesses the DB;
ready checks only local DB connectivity. Swagger documents business endpoints.

Apply `docker-compose.phase5.rollback.yml` LAST to restore only the three Node
implementations with their schema guard. Validate configuration before use. This
is a rollback configuration, not a claim that live rollback was exercised.
Never use down -v, truncate, reset AUTO_INCREMENT or remove orphan containers.

## Favorite contract

Physical table is `favorite_db.favorites` (lowercase), confirmed from running
MySQL with lower_case_table_names=1. The existing unique (userId,postId) index and
numeric auto-increment ID remain. Unmanaged Django mapping adds no migrations
or cross-service FK. HS256 JWT claims.id owns all three endpoints:

| External path | Contract |
|---|---|
| POST /favorites/toggle | Add 201 / remove 200, exact message/isFavorited |
| GET /favorites/check/:postId | Boolean object |
| GET /favorites/my-favorites | Raw hydrated Post[] |

No DELETE /favorites/:postId is added. Toggle does not validate Post existence.
Hydration uses POST_SERVICE_URL, finite timeout, request-ID forwarding and up to
eight concurrent HTTP calls in batches of eight, preserving row/result order.
Non-OK/unavailable/invalid JSON Post responses are omitted. No direct Post SQL.
Composite uniqueness remains DB-owned; concurrent races can return controlled
500 as legacy races do. Bearer HS256 strictness follows prior Python phases.

## Review contract and storage

Running `review_db.reviews` DOES contain nullable imageUrl, despite the historical
seed mismatch. reviewerId/revieweeId/postId are scalar IDs; postId is nullable.
All endpoints remain public:

| External path | Contract |
|---|---|
| GET /reviews/user/:userId | Raw newest-first array, rating/hasImage filters |
| POST /reviews | Raw 201 Review, multipart singular image |
| PUT /reviews/:id | Raw Review, truthy rating/comment only |
| DELETE /reviews/:id | 200 Review deleted successfully / missing 404 |

Create retains original numeric input types and omits absent optional fields;
reload returns database integers/nulls. Rating validation retains legacy 500
semantics. Truthy comment/rating values only update; empty comment cannot clear
existing content. No-op updates preserve stored timestamps. SQL comparisons keep
MySQL legacy coercion for lookup/filter strings rather than adding DRF validation.

Uploads reuse Phase 4 storage/WSGI patterns locally; no Python imports across
services. Safe basename, timestamp prefix, exclusive creation and local DB
transaction prevent overwrites and clean newly owned files on failed operations.
Chunked bodies spool above 256 KiB and are capped at Nginx's 50 MiB limit. Binary
serving remains canonical Django Post -> Gateway /uploads/*.

Successful replacement/deletion removes the exact old image when ownership can
be verified. Path traversal/hidden paths/symlink escapes are rejected. The file
is preserved if another Review references it or Post's HTTP image metadata
references it. If the finite Post ownership probe fails, cleanup is deferred and
logged; no new replacement file is removed after its DB commit. This fail-closed
behavior is intentional infrastructure divergence. Public write/ownership auth
and unrestricted upload MIME remain deferred security debt.

## Search contract and projection safety

Physical table `search_db.searchindices` is mapped unmanaged. postId is the PK,
without a new auto-increment ID. GET /search preserves approved-only filtering,
SQL LIKE on title OR description (including percent/underscore wildcards),
category/minPrice/maxPrice and createdAt DESC. No pagination/filter extensions.
Responses retain both postId and id=postId, price is a two-decimal STRING or null,
and timestamps use UTC ISO milliseconds Z. Post query's price remains numeric.

POST /search/sync remains public and returns 200 {message:"Index synced"}.
MySQL upsert inserts generated createdAt/updatedAt for new rows. Conflict updates
only supplied fields plus updatedAt; original createdAt and omitted optional
fields survive. Post timestamps in the request are ignored, matching the Node
handler. Generated Sequelize SQL was inspected with a mocked query to confirm
this policy. Post's Phase 4 business code/image are unchanged.

Read-only pre-migration audit: 4,463 source Posts, 4,872 projections, zero approved
Posts missing, 409 orphan projections. Matched field mismatches: title 11,
description 11, price 11, status 11, categoryId 8, categoryName 11, determinable
imageUrl 10; one source Post has ambiguous multiple image URLs. Counts overlap.
Category fallback is Đang cập nhật. This audit is separate from query parity.

Reconciliation performed: NO. Migration does not require changing legacy content.
No projection rows are removed, rewritten or rebuilt. Search content hashes and
HTTP response hashes are checked before/after. Future reconciliation requires a
separate bounded policy, snapshot, dry-run and explicit accounting; do not blindly
reuse legacy sync-all.js. Post remains the source of truth; Search never writes
back to Post DB. Admin Post delete still does not sync Search.

## Verification and isolated fixtures

Capture all eight schemas/counts, complete legacy row content hashes, repository
file hashes and upload inventory before writes. `tools/audit_phase5_search.py`
reports only counts/hash, never user content. Ignored `.artifacts/phase5` stores
runtime evidence, not credentials.

```powershell
.\.venv\Scripts\python.exe tools/verify_foundation.py
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe tools/prepare_phase5_tests.py
docker compose --env-file .env.python @phase5Stack -f docker-compose.phase5.test.yml --profile phase5-test up -d --no-deps favorite-phase5-node favorite-phase5-python review-phase5-node review-phase5-python search-phase5-node search-phase5-python post-phase5 message-phase5 dependencies-phase5 gateway-phase5
$env:PHASE5_TEST='1'
.\.venv\Scripts\python.exe -m pytest integration-tests/phase5 -vv -x
```

Prepare refuses pre-existing unowned schemas. Node references use unchanged source
mounted RO with the existing DDL guard. Node/Python writable rows and uploads are
separate; Review Python and Post fixture share only their test volume. No real
legacy rows are used as writable fixtures. Cleanup preserves unknown files and
removes only exact new names carrying the synthetic test prefix. Test DB cleanup
never resets IDs. Tests cover statuses, body keys/types, DB/file effects and
actual HTTP dependencies, not just mocks.

The Review fixture uses the canonical 3-second ownership-probe timeout. Its
replacement test warms the Post dependency after the explicit outage test, and
still requires the old image to disappear, the replacement to serve identical
bytes, and deletion to remove the replacement. A slow or unavailable Post probe
retains the file; that failure policy is tested separately.
The outage test refreshes Post's published URL after restart because Docker can
assign a different ephemeral host port, and waits for its readiness endpoint.
Internal dependency URLs keep the stable Docker service name and port 3003.

Apply `docker-compose.phase5.regression.yml` after `docker-compose.phase4.test.yml`
to run the complete unchanged Phase 4 suite with Django Search on its candidate
side and Django Favorite. Keep its Node reference side intact. Phase 2/3 fixtures
and their tests remain unchanged. Fixtures can run concurrently only when they
own separate schemas/volumes; NEVER run Phase 5 parity simultaneously with its
canonical E2E (both use owned Phase 5 Search/Message schemas).

## Guarded canonical E2E

The next Post ID can collide with a pre-existing Search projection. Apply the E2E
overlay LAST to make canonical Django Search use owned `phase5_search_e2e` and
route Post notifications to real unchanged Node Message clone. Post -> Search
still uses canonical search-service DNS. Canonical Auth/User/Post/Favorite/Review
use their existing DBs; Review/Post use the original shared upload volume.

```powershell
docker compose --env-file .env.python @phase5Stack -f docker-compose.phase5.e2e.yml up -d --no-deps search-service post-service
.\.venv\Scripts\python.exe tools/verify_phase5_runtime.py
# ALWAYS restore the normal stack, including on test failure:
docker compose --env-file .env.python @phase5Stack up -d --no-deps search-service post-service
.\.venv\Scripts\python.exe tools/verify_phase5_state.py --runtime --search-http --compare-content
.\.venv\Scripts\python.exe tools/audit_phase5_search.py --compare .artifacts/phase5/search-drift-before.json
.\.venv\Scripts\python.exe tools/verify_phase4_uploads.py --compare .artifacts/phase5/uploads-before.json
```

The verifier refuses ordinary Search/Message configuration before E2E writes,
requires mock email, verifies synthetic identity has no pre-existing dependent
rows, and journals only owned IDs/file hashes for recovery. It checks Auth JWT,
Favorite add/remove/check/hydration, Review replacement/delete/binary/range,
Post create/moderation/owner delete -> Django Search, and an actual existing file
hash. Cleanup guards rows with exact IDs/UUIDs and files with names/content hash.
Post container is temporarily recreated for notification isolation; its source
and image remain unchanged. Restore canonical search_db and Message URL, then
stop explicitly named fixtures without deleting volumes/schemas/orphans.
