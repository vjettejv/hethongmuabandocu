# Phase 4: Django Post + existing filesystem uploads

Gateway, Auth, User, Post and Category are Python. Message, Notification, Review,
Search and Favorite remain Node. Only Post's canonical container changes in this
phase; Gateway/Admin aliases and frontend are preserved. Use this document after
the historical Phase 1–3 reports. Phase 5 is not implemented.

## Runtime and safe cutover

Use the same Compose project (`kientrucpm`) and ignored `.env.python` containing
the existing shared JWT key, Django secret and DB credentials from Phase 2/3.
No new secret, database volume or host service port is introduced. Never print
`docker compose config` with environment values or container environment arrays.

```powershell
$phase4Stack = @('-f','docker-compose.yml','-f','docker-compose.phase2.yml','-f','docker-compose.phase3.yml','-f','docker-compose.phase4.yml')
docker compose --env-file .env.python @phase4Stack config --quiet
.\.venv\Scripts\python.exe tools/verify_runtime.py --snapshot .artifacts/phase4/db-before.json
.\.venv\Scripts\python.exe tools/verify_phase4_uploads.py --snapshot .artifacts/phase4/uploads-before.json
docker compose --env-file .env.python @phase4Stack build post-service
docker compose --env-file .env.python @phase4Stack up -d --no-deps post-service
```

Build/recreate only Post; do not rebuild Gateway/Auth/User/Category or use `down -v`.
Post retains port 3003, canonical DNS, original `post_db`, and the original
`shared_uploads:/app/uploads` mount also used by Node Review. The overlay removes
Node source/guard mounts and Node environment settings only from Python Post.
The Python image's default user remains appuser; the Post runtime overlay uses
the legacy root identity because the existing volume root is owned by root with
0755 permissions. No legacy chmod/chown is performed. This is local runtime debt.
Health is DB-free; readiness runs a read-only DB probe. No migrate/makemigrations,
Sequelize sync, imports, table replacements or startup seeds are used.

## Route matrix

| Gateway path | Internal Post path | Runtime/behavior |
|---|---|---|
| `/posts` | `/` | Django GET raw array / POST raw create envelope |
| `/posts/my-posts` | `/my-posts` | Django JWT claims.id |
| `/posts/:id` | `/:id` | Django public GET / owner DELETE |
| `/admin/posts*` | `/admin/posts*` | Django JWT, no role check |
| `/posts/admin/posts*` | `/admin/posts*` | Preserved legacy alias |
| `/uploads/*` | `/uploads/*` | Django raw binary, GET/HEAD/single Range |

No redirects are needed for no-slash or trailing-slash API spellings. Admin and
my-posts routes precede the parameter route. Gateway code and route stripping
stay unchanged; CORS remains Gateway-owned. Internal browser CORS is empty.

## Mapping and serialization

Post and Image are unmanaged models for `posts` and `images`, with explicit
legacy camelCase columns. Numeric IDs are AutoFields. userId/categoryId remain
scalar integers; only Image→Post is a local FK. The existing FK is CASCADE in
MySQL; Django maps DO_NOTHING and commands explicitly delete image metadata in
the same local transaction. No cross-service model imports or SQL are used.

List filters only categoryId/status/keyword when truthy; unfiltered list does
not imply approved status. Keyword uses parameterized SQL LIKE and retains
percent/underscore wildcards, collation, and Express's failed URI-decode fallback.
List/my/admin use a single LEFT JOIN ordered createdAt DESC, preserving observed
legacy image ordering; detail/admin writes load images separately without a new
filename ordering. One Category HTTP fetch enriches each query, including empty
lists. Invalid/non-OK Category responses fall back to `Đang cập nhật`.

Query price is a JSON number. Create preserves original price/category input
types (multipart strings; JSON numbers/strings), defaults status to available,
uses JWT userId, ignores body userId/status, and omits absent description/condition.
Create's response excludes Images/Category even after an upload: Node attaches
Images outside Sequelize dataValues, while its Search helper still uses that
first image. GET reload returns Images/Category and persisted nulls. Admin update
returns DB DECIMAL price as a fixed two-decimal string, includes Images and omits
Category. Persisted decimal rounding follows MySQL half-up behavior; raw create
retains the input. UTC ISO timestamps have milliseconds and Z, while the existing
DATETIME columns retain seconds on reload.

Missing detail and missing/non-owned owner delete are 404 with their distinct
error messages. Missing admin update is 404 `Not found`, verified from the actual
controller. Missing admin delete remains 200 `Deleted`. Required create fields
retain legacy 500 notNull messages; malformed decimal inputs and unexpected DB
errors remain 500 with controlled messages rather than exposing SQL details.

## HTTP dependencies

Category GET uses CATEGORY_SERVICE_URL once after local create/update/delete
commits. It enriches and does not validate category existence. Search sync and
Message notification use small explicit HTTP functions in posts/clients.py,
environment URLs, request ID forwarding, finite timeout and safe metadata logs.
No Auth verify roundtrip, cross-DB access, broker, cloud storage or distributed
transaction is added. Side effects remain asynchronous best effort. Each worker
has four HTTP threads and at most 64 outstanding calls; capacity failures log
metadata and drop delivery. Shutdown/crash can lose work; there is no durable
queue, retry or delivery guarantee. A dependency failure does not undo Post writes.

Search POST /sync includes postId/title/description/price/categoryId/imageUrl/
categoryName/status in camelCase. Omitted create description stays omitted in
the payload. Create sends available, not approved. Moderation always syncs,
including no-op updates. Owner delete sends deleted and null imageUrl because
the legacy owner lookup has no Images. Admin delete intentionally never syncs.
Search's own public queries still return approved only. Admin delete can leave
stale Search projections; this remains documented debt.

Only transitions to approved/rejected notify Message POST /notifications with
receiverId/title/message; no link, email service or Socket.IO implementation is
added. Repeating a status does not notify. Exact Vietnamese strings are tested
against Node and actual Node Message records in owned clones.

## Upload transport and safety

Files use sanitized basename and millisecond timestamp prefixes; stored URLs
remain `/uploads/<filename>`. Up to five files named images are accepted, without
MIME/extension restrictions. Wrong fields/over-five requests retain 500
`{error:"Internal Server Error",details:"Unexpected field"}`. Files use exclusive
creation; collision advances the timestamp and never replaces an existing file.
Post/Image writes are atomic; a failed operation removes only paths it created.
Owner/admin deletes leave physical files, matching Node.

Static serving resolves paths under the existing root, rejects hidden components
and symlink escapes, serves binary content with MIME/length/conditional caching,
HEAD and single byte ranges. Range bounds that cannot be satisfied return 416;
static misses are empty 404 responses rather than Express's HTML page. Multiple
ranges are treated as a full response. No full media streaming redesign is added.

Gunicorn terminates decoded chunked bodies but Django assumes absent Content-Length
means empty. A Post-only WSGI adapter reads in 64 KiB pieces into a disk-spooled
temporary file, sets the true length and then invokes Django. Memory spooling is
limited to 256 KiB; the chunked body cap is 50 MiB, matching Nginx's 50M body limit.
Known-length multipart uses Django's ordinary temporary upload handlers. Gateway
keeps streaming; no Gateway/frontend changes are necessary. A 6 MiB two-file
chunked upload, binary retrieval/range/HEAD/304 and post-delete bytes are tested.

Intentional differences: Bearer HS256 only, controlled malformed/DB/parser errors,
bounded dependency timeout/capacity, transactional metadata/failed-file cleanup,
safe basename/collision/containment, chunked body cap and static miss/range handling.
Deferred debt: admin role enforcement, arbitrary upload MIME, retained orphan files,
stale Search on admin delete, non-durable delivery and root upload permissions.

## Verification and isolated E2E

```powershell
.\.venv\Scripts\python.exe tools/verify_foundation.py
.\.venv\Scripts\python.exe tools/prepare_phase4_tests.py
docker compose --env-file .env.python @phase4Stack -f docker-compose.phase4.test.yml --profile phase4-test build post-reference
docker compose --env-file .env.python @phase4Stack -f docker-compose.phase4.test.yml --profile phase4-test up -d --no-deps post-reference post-candidate search-phase4-node search-phase4-python message-phase4-node message-phase4-python dependencies-node dependencies-python favorite-phase4 gateway-phase4
$env:PHASE4_TEST='1'
.\.venv\Scripts\python.exe -m pytest integration-tests/phase4 -q
```

Clones are phase4_post_node/python, phase4_search_node/python,
phase4_message_node/python and phase4_favorite_test. They copy schema only,
preserve the Post/Image FK, refuse pre-existing unowned schemas and never reset
auto-increment. Reference Node code is mounted read-only with the DDL guard.
Capture transports forward synthetic HTTP to actual unchanged Node handlers,
and Category reads the canonical Django service. All test ports bind loopback
with random numbers. Test upload volumes are only fixture volumes; production
Post continues using the original shared_uploads. Cleanup tracks exact newly
created fixture names and preserves unknown pre-existing entries.

The runtime snapshot found a legacy Search projection already occupying the next
Post auto-increment ID. Sending an ordinary synthetic create to legacy Search
would overwrite it. Therefore canonical E2E temporarily uses an explicit LAST
overlay for Post's Search/Message URLs, forwarding to real Node schema clones:

```powershell
docker compose --env-file .env.python @phase4Stack -f docker-compose.phase4.e2e.yml up -d --no-deps post-service
.\.venv\Scripts\python.exe tools/verify_phase4_runtime.py
docker compose --env-file .env.python @phase4Stack up -d --no-deps post-service
.\.venv\Scripts\python.exe tools/verify_runtime.py --compare .artifacts/phase4/db-before.json
.\.venv\Scripts\python.exe tools/verify_phase4_uploads.py --compare .artifacts/phase4/uploads-before.json
```

Do not run runtime E2E concurrently with parity tests: they share owned Search/
Message clones. The verifier refuses canonical Search/Message URLs, creates a
UUID synthetic Auth user, verifies OTP/profile/login, uploads through canonical
Gateway/Post, checks Category/price/images, hydrates through canonical Node Favorite,
moderates through real Node clones, owner-deletes, checks existing/prewritten files
and Review bytes, then removes only owned rows/files. It never exposes JWT/OTP/
password or legacy filenames. Restore the normal overlay even if E2E fails.
The final Post URLs are canonical Node Search/Message; the E2E overlay is not part
of normal runtime. Reuse Phase 2/3 fixture commands from their historical docs
and rerun both integration suites. Stop only the explicitly named fixture services;
do not delete volumes or schemas.

## Rollback

Apply docker-compose.phase4.rollback.yml last to restore only Node Post with the
schema guard and original shared upload mount. This is a configuration-validated
rollback path, not a claim of a live rollback test. It keeps Python Gateway/Auth/
User/Category. Remove the rollback overlay and recreate only Post to return to
Django. Preserve the Node reference image and source, all DBs and upload volumes.
