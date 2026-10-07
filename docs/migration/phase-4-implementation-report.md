# PHASE 4 IMPLEMENTATION REPORT

## 1. Summary

Hoàn tất Django Post trên port 3003, giữ post_db/posts/images và volume upload cũ.
Gateway/Auth/User/Category tiếp tục chạy Python. Category, Search, Message,
Favorite và upload đã được kiểm tra xuyên service; không triển khai Phase 5.

## 2. Starting State

Workspace: `D:\workspacecuachjp\KienTrucPM`; repository hethongmuabandocu.
Branch `develop`, HEAD `92777b8f70b6717e3ffd12657c725b2ea4e3d0ab` giữ nguyên.
Worktree đã có toàn bộ Phase 1–3 chưa commit và HUONG_DAN_TRIEN_KHAI.md untracked.
Snapshot trước Phase 4 gồm 447 file. Post canonical ban đầu là Node; Python Post
chỉ có foundation. Docker Desktop được khởi động lại trước snapshot/runtime checks.

## 3. Final Hybrid Architecture

```text
React/Nginx :80 -> FastAPI Gateway :3000
                  ├─ Django Auth       :3001
                  ├─ Django User       :3002
                  ├─ Django Post       :3003
                  ├─ Django Category   :3004
                  ├─ Node Message      :3005
                  ├─ Node Notification :3006 (mock email local)
                  ├─ Node Review       :3007
                  ├─ Node Search       :3008
                  └─ Node Favorite     :3009

Post -> Category/Search/Message qua HTTP
Favorite -> Post qua HTTP
Post + Review -> cùng shared_uploads:/app/uploads
```

Tám DB/volume gốc được giữ. Không đổi frontend, Node business source hoặc Gateway.

## 4. Gateway Route Matrix

| External | Internal Post | Runtime |
|---|---|---|
| `/posts` | `/` | Django GET/POST |
| `/posts/my-posts` | `/my-posts` | Django |
| `/posts/:id` | `/:id` | Django GET/DELETE |
| `/admin/posts*` | `/admin/posts*` | Django |
| `/posts/admin/posts*` | `/admin/posts*` | Django alias |
| `/uploads/*` | `/uploads/*` | Django binary |

Gateway giữ các quy tắc strip/preserve prefix, streaming, CORS và Socket.IO.

## 5. Post Architecture

posts/models.py ánh xạ DB; selectors.py giữ JOIN/filter/read; serializers.py có
response builders theo endpoint; services.py xử lý transaction/writes; views.py
giữ HTTP/envelope; authentication.py xác minh JWT local; clients.py xử lý ba
dependency HTTP; storage.py lưu/serve file; schema.py/urls.py giữ route/OpenAPI.
common/chunked.py thích nghi terminated Gunicorn input cho Django multipart.

## 6. Database Mapping

`posts` và `images`: managed=False, AutoField numeric ID, camelCase db_column rõ
ràng. price là DECIMAL(10,2); description/status/condition nullable đúng bảng cũ.
userId/categoryId là scalar. Image.post dùng FK nội bộ với db_column postId và
related_name Images; Django DO_NOTHING, command xóa metadata tường minh trong
transaction. FK CASCADE hiện có trong MySQL không đổi. Không có FK/model import
liên service; không chạy migrations/sync/seeds trên legacy DB.

## 7. Post Endpoint Matrix

| Endpoint | Node | Django | Parity đã kiểm tra |
|---|---|---|---|
| GET /posts | Raw array, filters | Tương đương | PASS |
| GET /posts/my-posts | JWT owner array | Tương đương | PASS |
| GET /posts/:id | Public enriched / 404 | Tương đương | PASS |
| POST /posts | 201 message/post raw | Tương đương | PASS |
| DELETE /posts/:id | Owner / 404 | Tương đương | PASS |
| GET /admin/posts | JWT, data array | Tương đương | PASS |
| PUT /admin/posts/:id | Raw data / 404 | Tương đương | PASS |
| DELETE /admin/posts/:id | 200 Deleted kể cả missing | Tương đương | PASS |
| GET/HEAD /uploads/* | Binary, normal range | Tương đương | PASS |

Malformed/error/static hardening khác biệt được tách riêng ở mục 18.

## 8. Price Serialization

Query/list/detail/admin-list: JSON number, không phải chuỗi Decimal. Create giữ
kiểu input: multipart string; JSON number/string. Admin update giữ chuỗi DB hai
chữ số thập phân. Create không có Images/Category; query có cả hai; admin update
có Images, không có Category. Mô phỏng cả hành vi Sequelize bỏ optional undefined
khỏi create nhưng GET reload trả null. Kiểm tra integer/decimal/invalid/empty/
missing price, description omitted/empty/null và MySQL half-up, gồm 1.225 -> 1.23.

## 9. JWT Compatibility

PASS Node HS256 tokens và token login từ Django Auth. claims.id quyết định owner
và creator; body userId/status không quyết định identity/default create status.
Missing, invalid, expired và wrong-signature được kiểm tra trên cả sáu protected
route/method combinations. Không gọi Auth verify cho từng request. Bearer/HS256
strictness theo Phase 2/3 là divergence đã công bố.

## 10. Category Integration

PASS Django Post -> canonical Django Category. Một GET/list mapping cho mỗi query
hoặc command cần enrichment; không N+1 HTTP. Giữ Category capitalization, dữ liệu
category thực và fallback Đang cập nhật. Category ID không tồn tại vẫn được tạo
theo Node; không thêm validation/FK. Outage/non-JSON/timeout fallback được kiểm tra.

## 11. Search Integration

PASS HTTP tới unchanged Node Search trên schema clones, kiểm tra payload và rows:
create -> available/first image; moderation -> approved/rejected/pending/custom/
null; no-op vẫn sync; owner delete -> deleted/imageUrl null. Search GET chỉ trả
approved. Admin delete không sync. Search failure không làm create/moderation
thất bại. Payload giữ camelCase và bỏ description khi create không gửi field.
Canonical Search DNS/HTTP được kiểm tra chỉ đọc từ container Django Post.

Snapshot cho thấy next Post ID đã có projection trong Search legacy. Canonical
E2E vì vậy route synthetic side effects tới real Node clones, không ghi đè
Search legacy. Overlay tạm được gỡ; URL cuối là search-service:3008.

## 12. Message Integration

PASS Django Post -> real Node Message clone. Chỉ transition tới approved/rejected
tạo notification; lặp status không tạo thêm. Kiểm tra exact receiverId/title/
message tiếng Việt và rows trong notifications. Không gửi link/email, không
migrate Socket.IO. Failure giữ Post status update thành công. Canonical Message
DNS/HTTP được kiểm tra chỉ đọc; URL cuối là message-service:3005.

## 13. Favorite→Post Regression

PASS unchanged Node Favorite -> Django Post: clone và canonical E2E. Raw favorite
array hydrate đủ price number, Images, Category, timestamps; missing/deleted Post
bị lọc, empty favorites/fallback Category hoạt động. Canonical add Favorite giữ
201 của Node. Không thay Favorite code hoặc schema; fixture được xóa có guard.

## 14. Upload Architecture

Canonical Post/Review cùng volume `kientrucpm_shared_uploads` tại /app/uploads RW.
URL metadata giữ /uploads/<timestamp>-<basename>. File dùng exclusive creation,
safe basename và containment; không cloud/object storage. Post runtime giữ root
identity như Node để viết volume root-owned 0755 mà không chmod/chown file cũ.

## 15. Multipart Compatibility

PASS 0/1/5 images, reject 6/wrong field với envelope legacy; arbitrary binary MIME;
multipart strings; JWT owner; metadata/byte order; transactional rollback và chỉ
xóa file của operation bị lỗi. PASS stream nhiều chunk với hai file, file lớn
6 MiB, binary/range/HEAD/304 qua Gateway. Gunicorn adapter spool ra disk, cap body
chunked 50 MiB; Nginx đang chạy được xác nhận client_max_body_size 50M.

## 16. Existing File Compatibility

PASS prewritten synthetic file trên Node/Django fixtures và shared volume thật.
Một file pre-existing thực được lấy qua Gateway và so SHA256, không in filename.
Node Review đọc đúng bytes của file do Django Post ghi. Inventory toàn bộ 46
entries khớp trước/sau: size/hash/symlink targets và không còn file test thừa.

## 17. Admin Routes

Canonical /admin/posts và /admin/posts/:id, aliases /posts/admin/posts* đều PASS;
no-slash/trailing slash không redirect. JWT required; role không được enforce như
Node. GET data array, PUT raw data, DELETE Deleted được giữ. Missing PUT là 404
Not found theo controller thực, không dùng giả định audit trước đó.

## 18. Intentional Divergences

Bearer HS256 only; controlled malformed/DB/parser error text thay vì SQL/details;
atomic Post/Image writes và cleanup file riêng khi failure; safe basename, no
collision overwrite, containment/dotfile/symlink checks; finite dependency
timeout/capacity; chunked body cap khớp Nginx; static miss empty 404 và unsatisfiable
single range 416. Core valid API parity được kiểm tra riêng với các thay đổi này.

## 19. Security Debt Deferred

Admin chỉ kiểm tra JWT, chưa role-check. MIME upload tự do; file vật lý giữ sau
delete. Admin delete có thể để stale Search. Async HTTP không durable/retry/broker;
capacity/shutdown có thể mất delivery. Post local chạy root vì volume permissions.
Internal Search sync và Message notification vẫn chưa có authentication như Node.
Không âm thầm sửa debt hoặc triển khai Phase 5.

## 20. Tests

Các lệnh đã chạy từ workspace, với .venv Python và environment của fixture:

```powershell
.\.venv\Scripts\python.exe tools/verify_foundation.py
.\.venv\Scripts\python.exe -m pytest integration-tests/phase4 -vv -x
.\.venv\Scripts\python.exe -m pytest integration-tests/phase4/test_cross_service.py integration-tests/phase4/test_post_parity.py::test_json_create_raw_types_nulls_defaults -vv -x
.\.venv\Scripts\python.exe -m pytest integration-tests/phase3 -vv
.\.venv\Scripts\python.exe -m pytest integration-tests/phase2 -vv
.\.venv\Scripts\python.exe tools/verify_phase4_runtime.py
.\.venv\Scripts\python.exe tools/verify_phase4_state.py
.\.venv\Scripts\python.exe tools/verify_runtime.py --compare .artifacts/phase4/db-before.json
.\.venv\Scripts\python.exe tools/verify_phase4_uploads.py --compare .artifacts/phase4/uploads-before.json
```

| Kiểm tra | Kết quả thực |
|---|---|
| Local foundation | 22/22 commands, 388 tests PASS |
| Full Phase 4 integration run | 96 PASS, lúc suite có 96 cases |
| Final image focused run | 35 PASS: 34 rechecks + 1 case create Search failure mới |
| Phase 4 distinct cases | 97 PASS qua hai run; 131 executions, không cộng lại thành 131 unique tests |
| Phase 3 sau Post cutover | 51 PASS |
| Phase 2 sau Post cutover | 35 PASS |
| Canonical E2E | PASS toàn flow và guarded cleanup |
| DB/file/runtime preservation | PASS |

Local breakdown: Auth 40, User 52, Post 69, Category 34, Message/Notification/
Review/Search/Favorite mỗi service 16, Gateway 99, contract tests 14. Không skip
test. Một StarletteDeprecationWarning có sẵn từ Gateway; không đổi dependency
Gateway trong Phase 4. Các failure được sửa và chạy lại; final logs nằm trong
ignored .artifacts/phase4, không lưu credentials.

## 21. Phase 2 Regression

35/35 PASS sau Post trở thành Django. Gồm Auth parity, Gateway multipart/streaming,
Node Socket.IO polling/upgrade/namespace và Nginx/CORS paths thực. Source/images
Gateway/Auth giữ nguyên. Một run trước cutover cũng đạt 35/35.

## 22. Phase 3 Regression

51/51 PASS sau cutover: User/Category parity và các cross-service tests. Container
IDs/images/start times User/Category không đổi; không rebuild. Run trước cutover
cũng đạt 51/51. Historical Phase 3 reports/contracts/source giữ nguyên.

## 23. Docker Verification

Các lệnh runtime đã dùng (secrets lấy từ environment hiện có, không in ra):

```powershell
$phase4Stack = @('-f','docker-compose.yml','-f','docker-compose.phase2.yml','-f','docker-compose.phase3.yml','-f','docker-compose.phase4.yml')
docker compose --env-file .env.python @phase4Stack config --quiet
docker compose --env-file .env.python @phase4Stack -f docker-compose.phase4.rollback.yml config --quiet
docker compose --env-file .env.python @phase4Stack build post-service
docker compose --env-file .env.python @phase4Stack up -d --no-deps post-service
```

Runtime + rollback overlay config --quiet PASS; rollback chỉ được validate config,
chưa execute live. Build chỉ post-service bằng Dockerfile.python. up -d --no-deps
chỉ recreate Post; canonical Post image kientrucpm-post-python-phase4 healthy,
3003, post_db, đúng shared volume. Five Python services health/ready PASS; các
Node dependencies vẫn running. Kiểm tra deployed business OpenAPI và canonical
Category/Search/Message HTTP PASS. E2E overlay đã gỡ, URLs canonical đã restore.
24 test containers được stop tường minh, không xóa volumes/schemas/orphans.

## 24. Database Safety

```text
post_db unexpected schema changes: NONE
all eight legacy schema fingerprints/row counts: UNCHANGED
```

Post fingerprint giữ `960c28a396f4f97e14a8ff7809a60a3b2f1826a291dd71c9130fb3cdce7a2ec1`.
Counts giữ Auth users 244; User profiles 6; Post posts 4,463/images 35; Category 5;
Message messages 31/notifications 2; Review 4; Search 4,872; Favorite 3. Tools
fingerprint column types/null/defaults, indexes, constraints/FK actions và case
setting; không checksum mọi business value. Cleanup chỉ ID/UUID owned fixtures;
không reset auto-increment. Test-only FK DDL chỉ nằm trong owned clone schemas.

## 25. Filesystem Safety

```text
pre-existing upload files lost: NONE
46 pre-existing upload entries/bytes: UNCHANGED
extra files remaining in shared uploads: NONE
```

Successful canonical E2E tạo và dọn 3 files; run verifier trước đó tạo 2 files đã
được dọn bằng UUID/ID/hash guards rồi xác nhận baseline. Tổng 5 shared test files
đã removed. Fixture-volume files được dọn theo exact new names sau mỗi case;
unit filesystem artifacts riêng nằm trong ignored .artifacts/phase4/unit-files.
Không rename/chmod/chown/delete file legacy; Review mount vẫn RW cùng volume.

## 26. Files Created

32 files, gồm 11 Post modules, chunked adapter, 3 Post test files, 4 Compose
overlays, Phase 4 contract, 4 integration-test files, 5 tools/transport files và
3 migration docs. Danh sách đầy đủ trong phase-4-files.md, tạo từ baseline hash.

## 27. Files Modified

8 Post foundation files: .env.example; common/logging.py; config/settings.py,
config/urls.py, config/wsgi.py; requirements.txt, requirements.lock.txt;
tests/test_health.py. Tất cả 439 baseline files còn lại giữ SHA256, gồm frontend,
Node code, seeds, Phase 1–3 work và HUONG_DAN_TRIEN_KHAI.md.

## 28. Git Status

Branch/HEAD giữ nguyên; không stage/commit/push. .gitignore tracked modification
đã có từ Phase 1, giữ hash trước Phase 4. Migration files Phase 1–4 còn untracked,
nên Git status không tách được các edits trong Post foundation cũ; manifest SHA256
tách riêng 32 new/8 modified của Phase 4. HUONG_DAN_TRIEN_KHAI.md còn nguyên và
untracked. Các manifest Phase 1–3 trước đó không đổi.

## 29. Known Issues

Debt tại mục 19 vẫn tồn tại. Legacy Search dataset có projection ở next Post ID
được kiểm tra trước E2E; cần audit drift khi lập Phase 5/live data tests, không
cleanup legacy projection trong migration này. Rollback live chưa diễn tập;
multiple-range/full media streaming không được mở rộng. DB safety không phải
full-row checksum. Không còn failure/blocker Phase 4 chưa xử lý.

## 30. Phase 5 Readiness

Sẵn sàng nền tảng cho FAVORITE + REVIEW + SEARCH: Post contracts, numeric IDs,
shared upload interface và HTTP integrations đã được xác nhận. Chưa migrate ba
service đó. Khi lập Phase 5 phải tiếp tục dùng owned fixtures, giữ shared volume,
snapshot DB/files và xét Search projection drift trước ghi dữ liệu live.

## 31. Suggested Commits

Suggestions only; chưa thực hiện:

```text
feat(posts): migrate post service to Django
feat(posts): preserve legacy filesystem uploads
test(posts): add Node Python post contract parity
test(posts): add category search message integration tests
test: add favorite to Django post regression
docs: document phase 4 migration
```
