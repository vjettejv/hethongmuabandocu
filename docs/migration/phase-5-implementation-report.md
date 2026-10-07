# PHASE 5 IMPLEMENTATION REPORT

## 1. Summary

Đã migrate Favorite 3009, Review 3007 và Search 3008 sang Django/DRF. Canonical cutover và guarded E2E đã PASS. Full Phase 5 103/103 PASS; foundation442 PASS,22/22 commands; Phase 2/3/4 regression35/51/97 PASS. Canonical đang dùng cấu hình bình thường sau E2E. Không triển khai Phase 6.

## 2. Starting State

Workspace `D:\workspacecuachjp\KienTrucPM`, branch `develop`, HEAD `92777b8f70b6717e3ffd12657c725b2ea4e3d0ab`. Worktree Phase 1–4 đã dirty/untracked. Baseline 479 files, tám DB và 46 upload entries; HUONG_DAN_TRIEN_KHAI.md được bảo toàn.

## 3. Final Hybrid Architecture

Python: Gateway3000, Auth3001, User3002, Post3003, Category3004, Review3007, Search3008, Favorite3009. Node: Message3005, Notification3006. Frontend/Nginx80 giữ nguyên. Favorite→Post HTTP; Post→Search HTTP; Review/Post cùng shared_uploads.

## 4. Gateway Route Matrix

| External | Internal | Runtime |
|---|---|---|
| /favorites/toggle, /favorites/check/:postId, /favorites/my-favorites | Strip /favorites | Django Favorite |
| /reviews, /reviews/user/:userId, /reviews/:id | Strip /reviews | Django Review |
| /search, /search/sync | Strip /search | Django Search |
| /uploads/* | Preserve path | Django Post |

Gateway code modified: NO. Gateway image rebuilt: NO. Routes/prefixes/CORS/Socket.IO giữ Phase 4.

## 5. Favorite Architecture

favorites/models.py mapping; services.py toggle atomic; selectors.py checks/rows; authentication.py JWT local; clients.py parallel hydration; views.py/http.py giữ envelopes/errors; urls.py/schema.py routes/OpenAPI. Không thêm DELETE API.

## 6. Favorite Database Mapping

Actual table `favorite_db.favorites`, lowercase; MySQL lower_case_table_names=1. managed=False, explicit camelCase columns, numeric AutoField id và unique (userId,postId) hiện có. Không FK/cross-DB SQL/migration/sync.

## 7. Favorite Endpoint Matrix

| Endpoint | Node | Django | Parity |
|---|---|---|---|
| POST /favorites/toggle | Add201/remove200 exact messages | Giữ contract | PASS |
| GET /favorites/check/:postId | {isFavorited:boolean} | Giữ contract | PASS |
| GET /favorites/my-favorites | Raw hydrated Post[] | Giữ contract | E2E PASS |

Missing postId giữ exact WHERE undefined error; null giữ notNull error. Không validate Post existence. Composite uniqueness vẫn DB-owned.

## 8. Favorite→Post Integration

E2E PASS canonical Django Favorite→Django Post, JWT login từ Django Auth. Kiểm tra price numeric, Images/Category/timestamps, missing/deleted filtering. Parallel batches tối đa8 calls, timeout hữu hạn, request-ID forwarding, raw array/order; outage/non-JSON được lọc. Node Favorite reference vẫn giữ để parity.

## 9. Review Architecture

reviews/models.py; selectors.py; serializers.py riêng raw create/update/reload; services.py writes/transactions; storage.py save/ownership-safe unlink; views.py/http.py; urls.py/schema.py. Local common/chunked.py dùng proven Phase 4 pattern, không import business models/code xuyên service.

## 10. Review Database Mapping

Actual runtime `review_db.reviews` có nullable imageUrl varchar(255), khác seed lịch sử. managed=False; explicit reviewerId/revieweeId/postId/imageUrl/createdAt/updatedAt; postId nullable; scalar IDs, không FK tới Post/User. Không sửa physical schema.

## 11. Review Endpoint Matrix

| Endpoint | Node | Django | Parity |
|---|---|---|---|
| GET /reviews/user/:userId | Raw array newest-first, filters | Giữ contract | Parity run PASS |
| POST /reviews | Public raw201, image | Giữ contract | Parity/E2E PASS |
| PUT /reviews/:id | Truthy rating/comment | Giữ contract | Parity/E2E PASS |
| DELETE /reviews/:id | 200 message/missing404 | Giữ contract | Parity/E2E PASS |

Create giữ raw input types và bỏ absent optional fields; GET reload nulls/DB integers. Rating invalid giữ500 với controlled errors khi cần; no-op giữ timestamps; empty comment không clear.

## 12. Review Upload Compatibility

Canonical Review/Post cùng volume `kientrucpm_shared_uploads` RW tại /app/uploads. Singular image giữ /uploads/<timestamp>-<basename>. E2E Review→shared volume→Post→Gateway binary/range PASS; chunked fixture PASS. Không đổi global permissions/storage/static owner.

## 13. Review File Lifecycle

Create ghi exclusive file; DB failure cleanup chỉ file mới của operation. Replace thành công lưu URL mới, rồi unlink exact old file nếu ownership verified; delete tương tự. Sibling Review hoặc Post reference bảo vệ file; Post outage/path escape/symlink khiến giữ file. Unlink failure không xóa replacement đã commit. E2E A→B→delete PASS.

## 14. Search Architecture

search_app/models.py explicit projection; selectors.py approved/filter/LIKE; serializers.py Search-specific decimal/timestamps/id alias; services.py parameterized MySQL upsert; views/http/urls/schema. Không full-text engine, pagination, cross-DB SQL hoặc reverse Post writes.

## 15. Search Database Mapping

`search_db.searchindices`, managed=False. postId là IntegerField primary key, không AutoField. Explicit legacy fields title/description/price/categoryId/imageUrl/categoryName/status/createdAt/updatedAt. price nullable DECIMAL(10,2). Không replacement table/migrations.

## 16. Search Endpoint Matrix

| Endpoint | Node | Django | Parity |
|---|---|---|---|
| GET /search | Approved only, raw SearchIndex[], id alias | Giữ contract | Canonical response hashes PASS |
| POST /search/sync | Public200 Index synced, upsert | Giữ contract | Parity/E2E PASS |

LIKE wildcards/collation, category, min/maxPrice và createdAt DESC giữ nguyên. Upsert giữ original createdAt, update updatedAt; omitted optional fields giữ giá trị cũ; không copy Post timestamps.

Sync required-field errors giữ phân biệt Node thực tế: title=null → notNull Violation; thiếu/null postId → Column 'postId' cannot be null; có postId nhưng thiếu title → Field 'title' doesn't have a default value. Explicit null validation đứng trước missing-PK/default errors.

## 17. Search Price Serialization

Node và Django Search GET trả fixed2 decimal STRING hoặc null, ví dụ "123.45". Post query vẫn trả JSON number. Canonical E2E/response hashes xác nhận distinction. DB rounding theo MySQL HALF_UP, gồm1.225→1.23.

## 18. Search Drift Audit

Read-only before: Post4,463; Search4,872; approved Posts missing0; orphan Search409; matched4,463. Mismatch counts title11, description11, price11, status11, categoryId8, categoryName11, determinable imageUrl10; ambiguous image rows1. Counts overlap, không cộng thành số distinct stale Posts. Artifact ignored `.artifacts/phase5/search-drift-before.json` chỉ counts/hash.

## 19. Search Reconciliation

Reconciliation performed: NO. Không cần repair để migrate query/upsert runtime. Không truncate/delete/rebuild/update legacy projection hoặc chạy sync-all. Complete Search content hash/drift counts và canonical response hashes giữ nguyên sau cutover/E2E. Future reconciliation cần policy/snapshot/dry-run/accounting riêng.

## 20. Post→Search Integration

PASS canonical Post→canonical Django Search DNS: create available/first image, approved/rejected/approved moderation, owner delete deleted/null image. Search E2E dùng owned schema `phase5_search_e2e` trong existing search-db container để tránh next Post ID collision. Không ghi projection test vào legacy `search_db`. Message effects tới unchanged real Node clone. Normal search_db/Message URLs đã restore. Phase 4 Post source/image không đổi; admin delete vẫn không sync.

## 21. Intentional Divergences

Bearer HS256 strictness; bounded Favorite HTTP concurrency/timeout/request IDs; controlled malformed/DB/parser errors; atomic Review DB/file failure cleanup; safe basename/exclusive writes/path/symlink checks; ownership-safe post-commit unlink, giữ file khi probe unavailable/shared reference; chunked spool/body cap theo Nginx50M. Core valid API semantics được parity-test riêng. Không claim durable delivery/auth fixes.

## 22. Security Debt Deferred

Toggle chưa validate Post existence. Review writes public và body identity không gắn JWT. Search /sync public; internal authentication absent. Search drift/stale projections/admin delete model còn nguyên. Upload MIME tự do; Review/Post local root volume compatibility; fail-closed unlink có thể giữ orphan files. Post side effects vẫn best effort, không broker/retry/durability.

## 23. Tests

Local foundation: 442 PASS,22/22 commands sau Search fix cuối. Full Phase5 suite: 103/103 PASS,770.43s (12m50s). pip check PASS. Ruff check PASS,266 files already formatted. Canonical E2E PASS; tám DB schema/count/full-row content và46 upload entries PASS. Logs ignored `.artifacts/phase5`, final integration log `integration-final-complete.log`.

Lỗi fixture ở lần chạy trước: Review ownership probe timeout1s trong khi Post GET / trả200 sau1.933s. Fixture đã đặt3s giống canonical, và test lifecycle làm nóng Post sau test outage. Không đổi production code hoặc giảm assertion xóa file; targeted lifecycle recheck1/1 PASS16.63s; final full103/103 PASS. Các lỗi parity đã sửa theo Node reference gồm Favorite missing postId và Search upsert phải giữ createdAt trên conflict.

Full rerun tiếp theo phát hiện Docker đổi ephemeral host port của Post fixture từ61070 sang64173 khi start lại; session URL cache còn dùng cổng cũ. Test outage đã cập nhật published URL và chờ /ready trước khi trả lại dependency. Lỗi này thuộc test harness; canonical DNS/port3003 không thay đổi. Chuỗi outage→lifecycle đã PASS2/2 trong34.54s; full suite được chạy lại với nguyên assertions.

Lần full sau đạt100 PASS trước required-field error mismatch của Search. Node probe trên owned schema xác nhận ba error bodies khác nhau cho {}, {postId:1} và {postId:1,title:null}. Django service và local test đã sửa đúng thứ tự/phân biệt; chỉ Search image được rebuild/cutover lại. Không giảm assertion so sánh error body. Required-field recheck3/3 PASS27.62s; final full suite103/103 PASS. Các lần failure trước được giữ riêng trong ignored artifacts.

```powershell
.\.venv\Scripts\python.exe tools/verify_foundation.py
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
$env:PHASE5_TEST='1'
.\.venv\Scripts\python.exe -m pytest integration-tests/phase5 -vv -x
$env:PHASE2_TEST='1'
.\.venv\Scripts\python.exe -m pytest integration-tests/phase2 -vv
$env:PHASE3_TEST='1'
.\.venv\Scripts\python.exe -m pytest integration-tests/phase3 -vv
$env:PHASE4_TEST='1'
.\.venv\Scripts\python.exe -m pytest integration-tests/phase4 -vv
.\.venv\Scripts\python.exe tools/verify_phase5_runtime.py
.\.venv\Scripts\python.exe tools/verify_phase5_state.py --runtime --search-http --compare-content
.\.venv\Scripts\python.exe tools/audit_phase5_search.py --compare .artifacts/phase5/search-drift-before.json
.\.venv\Scripts\python.exe tools/verify_phase4_uploads.py --compare .artifacts/phase5/uploads-before.json
```

## 24. Phase 2 Regression

35/35 PASS sau canonical Phase5 cutover,183.40s; Gateway/Auth/Socket.IO/Nginx/CORS giữ nguyên.

## 25. Phase 3 Regression

51/51 PASS sau cutover,206.20s. User/Category/Phase3 historical code và fixtures giữ nguyên.

## 26. Phase 4 Regression

97/97 PASS sau canonical Phase5 cutover, 1,052.77s. Candidate side dùng Django Search/Favorite thông qua regression overlay; Node reference side giữ nguyên. Không sửa/skip/weaken Phase4 test assertions. Tên test lịch sử có chữ Node không thay đổi runtime candidate đã kiểm tra.

## 27. Docker Verification

Build ba images kientrucpm-{favorite,review,search}-python-phase5 và recreate chỉ ba canonical services. Runtime/rollback/test/regression Compose config --quiet PASS. Eight Python health/ready PASS; Node Message/Notification running. Original shared volume, canonical DNS/ports/JWT PASS. E2E overlay restore PASS. Rollback config validated, chưa live rollback.

```powershell
$phase5Stack = @('-f','docker-compose.yml','-f','docker-compose.phase2.yml','-f','docker-compose.phase3.yml','-f','docker-compose.phase4.yml','-f','docker-compose.phase5.yml')
docker compose @phase5Stack config --quiet
docker compose @phase5Stack -f docker-compose.phase5.rollback.yml config --quiet
docker compose @phase5Stack build favorite-service review-service search-service
docker compose @phase5Stack up -d --no-deps favorite-service review-service search-service
```

Shared env được lấy từ existing runtime, không in secrets. Gateway source/image không đổi. Post image/source unchanged; Post tạm recreate hai lần để isolate Message E2E rồi restore. Bảy container Gateway/Auth/User/Category/Message/Notification/frontend giữ IDs/images/start time. Đã dừng24 fixtures regression và10 fixtures Phase5, giữ containers/volumes/schemas; chỉ19 canonical containers chạy sau kiểm tra cuối.

## 28. Database Safety

```text
favorite_db unexpected schema changes: NONE
review_db unexpected schema changes: NONE
search_db unexpected schema changes: NONE
all eight legacy schema fingerprints/row counts: UNCHANGED
all complete legacy table content hashes: UNCHANGED
```

Favorite rows3; Review4; Search4,872; Post4,463/images35 giữ nguyên sau E2E. Cleanup exact IDs/UUIDs, no auto-increment reset. Test-only DDL chỉ owned empty clones. Drift unchanged; no reconciliation.

## 29. Filesystem Safety

```text
pre-existing upload files lost: NONE
before entries: 46
after cleanup entries: 46
shared test files created: 4
shared test files removed: 4
unexpected extras: 0
```

Review lifecycle dọn2 files; guarded final cleanup dọn2 Post files. Size/hash/symlink targets inventory unchanged. Không rename/chmod/chown/glob-delete file legacy. Fixture volumes cleanup exact owned new filenames; unit artifacts riêng ignored.

## 30. Files Created

55 files mới; danh sách đầy đủ tại [phase-5-files.md](phase-5-files.md#created), tạo từ baseline SHA256. Gồm ba app implementations, contract artifacts, local/integration tests, Compose overlays, audit/safety/E2E tooling và docs.

```text
contracts/favorites/phase-5.json
contracts/reviews/phase-5.json
contracts/search/phase-5.json
docker-compose.phase5.e2e.yml
docker-compose.phase5.regression.yml
docker-compose.phase5.rollback.yml
docker-compose.phase5.test.yml
docker-compose.phase5.yml
docs/migration/phase-5-files.md
docs/migration/phase-5-implementation-report.md
docs/migration/phase-5.md
favorite-service/favorites/authentication.py
favorite-service/favorites/clients.py
favorite-service/favorites/exceptions.py
favorite-service/favorites/http.py
favorite-service/favorites/models.py
favorite-service/favorites/schema.py
favorite-service/favorites/selectors.py
favorite-service/favorites/services.py
favorite-service/favorites/urls.py
favorite-service/favorites/views.py
favorite-service/tests/test_favorites.py
integration-tests/phase5/conftest.py
integration-tests/phase5/pytest.ini
integration-tests/phase5/test_cross_service.py
integration-tests/phase5/test_favorite_parity.py
integration-tests/phase5/test_review_parity.py
integration-tests/phase5/test_search_parity.py
review-service/common/chunked.py
review-service/reviews/exceptions.py
review-service/reviews/http.py
review-service/reviews/models.py
review-service/reviews/schema.py
review-service/reviews/selectors.py
review-service/reviews/serializers.py
review-service/reviews/services.py
review-service/reviews/storage.py
review-service/reviews/urls.py
review-service/reviews/views.py
review-service/tests/conftest.py
review-service/tests/test_reviews.py
search-service/search_app/exceptions.py
search-service/search_app/http.py
search-service/search_app/models.py
search-service/search_app/schema.py
search-service/search_app/selectors.py
search-service/search_app/serializers.py
search-service/search_app/services.py
search-service/search_app/urls.py
search-service/search_app/views.py
search-service/tests/test_search.py
tools/audit_phase5_search.py
tools/prepare_phase5_tests.py
tools/verify_phase5_runtime.py
tools/verify_phase5_state.py
```

## 31. Files Modified

21 files sửa; danh sách đầy đủ tại [phase-5-files.md](phase-5-files.md#modified). Chỉ Favorite/Review/Search foundation settings/urls/logging/requirements/env/health tests, Review WSGI; tools/verify_phase4_uploads.py chuyển inventory sang canonical Python Post để hoạt động xuyên Review cutover. 458 baseline files giữ nguyên, gồm Phase4 Post business, Gateway, Auth/User/Category, Node source/frontend/seeds/user guide.

```text
favorite-service/.env.example
favorite-service/common/logging.py
favorite-service/config/settings.py
favorite-service/config/urls.py
favorite-service/requirements.lock.txt
favorite-service/requirements.txt
favorite-service/tests/test_health.py
review-service/.env.example
review-service/common/logging.py
review-service/config/settings.py
review-service/config/urls.py
review-service/config/wsgi.py
review-service/requirements.lock.txt
review-service/requirements.txt
review-service/tests/test_health.py
search-service/.env.example
search-service/common/logging.py
search-service/config/settings.py
search-service/config/urls.py
search-service/tests/test_health.py
tools/verify_phase4_uploads.py
```

## 32. Git Status

Branch/HEAD unchanged; không stage/commit/push/reset/clean. Existing tracked .gitignore edit từPhase1 giữ nguyên; Phase1–5 migration work còn untracked, manifest separates Phase5 delta. HUONG_DAN_TRIEN_KHAI.md untouched/untracked.

## 33. Known Issues

Pre-existing Search drift chưa repair, public Review/Search APIs và các debt tại22 còn nguyên. File ownership probe cần HTTP Post; outage có thể defer unlink. Rollback chưa live rehearsal. Một existing Gateway StarletteDeprecationWarning giữ nguyên. Không còn test failure hoặc blocker migration Phase5. Không triển khai Phase6.

## 34. Phase 6 Readiness

Sẵn sàng bắt đầu PHASE 6 — MESSAGE + NOTIFICATION khi được yêu cầu; không còn blocker Phase5. Full regressions và canonical safety checks đã PASS. Hai service đó vẫn Node, Socket.IO/email business chưa migrate. Giữ mock email cho tests, tiếp tục clone fixtures và DB/upload/content snapshots. Search drift là debt riêng, không được cleanup lẫn vào Phase6 migration.

## 35. Suggested Commits

Suggestions only; chưa thực hiện:

```text
feat(favorites): migrate favorite service to Django
feat(reviews): migrate review service to Django
feat(search): migrate search service to Django
test(favorites): add Node Python favorite parity
test(reviews): add multipart and shared upload parity
test(search): add projection and sync parity
test: add post search and favorite post integrations
docs: document phase 5 migration and search drift
```
