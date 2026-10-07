# PHASE 2 IMPLEMENTATION REPORT

## 1. Summary

FastAPI Gateway và Django Auth đã được triển khai, hybrid runtime đang hoạt động.
REST vào Python Gateway; Auth dùng bảng users cũ; tám services còn lại vẫn là Node.
Local verification: 281 tests pass. Final integration: **35/35 pass** sau khi
restart Nginx để refresh DNS Gateway. E2E và DB checks pass. **Phase 2 hoàn tất**;
không triển khai Phase 3.

## 2. Starting State

Branch develop; HEAD `92777b8f70b6717e3ffd12657c725b2ea4e3d0ab`.
Phase 1 chưa commit: .gitignore modified, Python foundations/contracts/docs untracked.
Pre-existing HUONG_DAN_TRIEN_KHAI.md giữ nguyên. Snapshot 379 file đầu Phase 2 lưu
local để phân biệt thay đổi mới. Docker 29.8.2; trước cutover có 10 prototypes Python
và 8 MySQL containers chạy; chưa có Node business containers đang chạy.

## 3. FastAPI Gateway Architecture

Lifespan quản lý một httpx AsyncClient, streaming request/response, timeout có env,
không global JWT authorization. Gateway giữ body/query/status/content headers và
repeated headers; bỏ hop-by-hop headers, set upstream Host, truyền request ID và
forwarding metadata. Socket.IO transport dùng HTTP proxy + WebSocket frame bridge;
Node Message tiếp tục xử lý protocol. OpenAPI chỉ mô tả health/ready của Gateway.

## 4. Gateway Route Matrix

| Public Route | Target | Rewrite | Runtime |
|---|---|---|---|
| /auth/* | auth-service:3001 | Strip /auth | Django |
| /users/* | user-service:3002 | Strip /users | Node |
| /posts/* | post-service:3003 | Strip /posts | Node |
| /categories/* | category-service:3004 | Strip /categories | Node |
| /messages/* | message-service:3005 | Strip /messages | Node |
| /notifications/* | notification-service:3006 | Strip /notifications | Node |
| /reviews/* | review-service:3007 | Strip /reviews | Node |
| /search/* | search-service:3008 | Strip /search | Node |
| /favorites/* | favorite-service:3009 | Strip /favorites | Node |
| /admin/posts/* | post-service:3003 | Original path | Node |
| /admin/categories/* | category-service:3004 | Original path | Node |
| /uploads/* | post-service:3003 | Original path, binary | Node |
| /socket.io/* | message-service:3005 | Original path | Compatibility transport → Node |

Legacy aliases giữ nguyên: /posts/admin/posts, /categories/admin/categories,
/messages/notifications, /notifications/email. Không thêm /api hoặc /api/v1.
Auth infrastructure không được public thêm qua /auth/health hoặc /auth/ready.

## 5. Django Auth Architecture

authentication/models.py mapping unmanaged; selectors.py lookup; serializers.py
mô tả request/response Swagger; views.py kiểm soát envelopes/errors; urls.py năm
routes. services/ chia registration, login, otp, passwords, tokens, clients.
Không dùng Django auth framework, AbstractUser, SimpleJWT hoặc session tables.
Chưa thêm refresh/logout/forgot/reset endpoints.

## 6. Database Mapping

AuthUser -> auth_db.users; AutoField id, roleId, username/email unique, password,
isVerified, otp, createdAt/updatedAt. DB columns và nullable fields theo live metadata,
external projection giữ camelCase. managed=False; timestamps viết explicit UTC theo
cấu hình foundation, không đổi DB timezone. Không migrate/makemigrations/ALTER.

## 7. Endpoint Matrix

| Endpoint | Node | Django | Parity |
|---|---|---|---|
| POST /auth/register | 201 message/userId; 400 message | Same envelope/status | Tested new, missing fields, duplicates, unverified reuse, dependency outage |
| POST /auth/login | 200 token/user; 401 error | Same, including unverified login | Tested username/email, wrong/unknown credentials, both bcrypt prefixes |
| POST /auth/verify-otp | 200 message; 404 unknown; wrong OTP 500; bypass exists | 200/404 matched; wrong OTP 400; no bypass | Success/state/dependency matched; differences explicit |
| GET /auth/:id | Raw four-field user; 404 error | Same projection/status | Existing/missing tested; secrets excluded |
| POST /auth/verify | 200 valid/user claims; 401 error | Same for valid Bearer/errors; strict transport | Both runtime tokens/expiry/signature tested; non-Bearer divergence explicit |

Node source-derived baseline giữ nguyên. Phase 2 differences nằm ở
contracts/auth/phase-2.json. Không tuyên bố parity cho mọi malformed input/race/error.

## 8. Password Compatibility

Node-generated $2a$10$/$2b$10$ hashes đăng nhập được bằng Django. Python-created
bcrypt cost 10 hashes được bcryptjs/Node Auth xác thực. Không copy hash của người
dùng thật, không rehash rows legacy hoặc ép reset password. UTF-8 truncation ở 72
bytes được dùng để giữ bcryptjs semantics thay vì bcrypt 5 rejecting long input.

## 9. JWT Compatibility

Node→Python verify và Python→Node jsonwebtoken verify pass. Claims id/roleId/iat/exp
giữ nguyên, TTL 86400; token strings không được so sánh trực tiếp. Expired/wrong
signature/missing/malformed authorization được kiểm tra. Actual Python login JWT
được protected Node User /me chấp nhận qua Gateway. Shared key đọc env; không rotate.

## 10. Downstream Dependencies

Register gọi Node Notification POST /email với payload to/subject/text/html cũ.
OTP success save verified/clear OTP rồi Node User PUT /{id}, fullName=username.
USER_SERVICE_URL/NOTIFICATION_SERVICE_URL đọc env. Không ghi trực tiếp user_db từ
Auth. Downstream lỗi vẫn giữ Auth success/state theo Node; timeout mặc định 5s,
không retry write. Notification dùng mock mode hiện có; không gửi email thật.

## 11. Gateway Compatibility

99 Gateway tests gồm prefixes, methods, aliases, raw queries, headers/request IDs,
JSON, multipart, binary/gzip, redirects/repeated cookies, CORS và controlled errors.
Real-wire fixture xác minh multipart >1 MiB qua nhiều chunks, hash/body/boundary,
query và authorization metadata; binary/cache/ETag/cookies pass-through.
GET /posts và /categories thực tế qua Gateway trả 200; không tạo marketplace post.

## 12. Socket.IO Transition

Node Message giữ Socket.IO server. HTTP polling dùng streaming REST proxy;
WebSocket upgrade bridge chuyển frames nguyên protocol. EIO=4 polling/probe/upgrade
và namespace connect đã được kiểm tra qua Gateway và frontend Nginx. Test gửi room
join frame nhưng không tuyên bố room authorization hoặc toàn bộ message delivery
parity. Browser Origin localhost tiêu chuẩn được thêm allowlist và kiểm tra.

## 13. Intentional Behavior Divergences

- OTP bypass bị loại bỏ; OTP empty/cleared không thể verify.
- Sai OTP trả 400 với thông báo đọc được, thay lỗi mojibake/500 cũ.
- Auth verify chỉ chấp nhận Bearer và HS256; Node từng lấy token word thứ hai.
- Malformed login credentials trả controlled 401; register yêu cầu string fields.
- DB exceptions trả generic 500, không raw DB error có thể chứa dữ liệu.
- Gateway 502/504 và timeouts được kiểm soát; Auth downstream timeout có giới hạn.
- CORS allowlist thay unrestricted CORS; local frontend origins được kiểm chứng.
- Runtime Node schema sync/DDL bị chặn; không sửa business source Node.

## 14. Security Debt Deferred

Login vẫn cho unverified accounts theo parity. OTP expiry/retry/rate limits chưa có.
Unverified account reuse, public User writes, Post admin checks, Review writes,
Search sync, Socket rooms và internal trust vẫn là debt đã ghi nhận. Không đổi
JWT architecture/rotate key; strength/secret debt legacy chưa xử lý ở phase này.

## 15. Tests

Exact local runner: `.venv/Scripts/python.exe tools/verify_foundation.py`:
22/22 commands, 281 tests (40 Auth + 128 remaining Django + 99 Gateway + 14 baseline).
Ruff check/format, 9 local Django checks và pip check pass. Gateway có một upstream
Starlette TestClient/httpx deprecation warning; không weaken tests hoặc lint.
Live runner: PHASE2_TEST=1 rồi `python -m pytest integration-tests/phase2 -q`.
**35 passed in 113.18s** trong final rerun. Tests dùng explicit schema clones và real
Node/Django services; fixtures/mock chỉ dành cho email và transport không ghi Post.

## 16. Docker Verification

Baseline/Phase2/test Compose config pass; actual Gateway/Auth builds/start pass.
Python Gateway/Auth healthy; remaining eight business services Node; 8 DBs hiện có.
Canonical DNS/ports giữ nguyên. Auth manage.py check trong Linux container pass,
/ready report database connected. Không xóa Phase 1 prototypes; chỉ stop chúng.
Rollback overlay có guard; config validation pass, không chạy rollback tự động.

Các lệnh Docker đã thực hiện với runtime variables được cấp trong process, không
ghi secrets vào report hoặc tạo file env chứa credentials:

```powershell
docker compose -f docker-compose.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.phase2.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.phase2.yml -f docker-compose.phase2.test.yml --profile phase2-test config --quiet
docker compose -f docker-compose.yml -f docker-compose.phase2.yml -f docker-compose.phase2.rollback.yml config --quiet
docker compose --parallel 1 -f docker-compose.yml -f docker-compose.phase2.yml build api-gateway auth-service
docker compose -f docker-compose.yml -f docker-compose.phase2.yml up -d --no-deps api-gateway auth-service user-service post-service category-service message-service notification-service review-service search-service favorite-service
docker compose -f docker-compose.yml -f docker-compose.phase2.yml restart frontend
docker exec auth-service python manage.py check
```

Kết thúc: 19 containers runtime đang chạy; Gateway/Auth healthy. Sáu test services
đã stop; ba test schemas còn giữ lại, không còn synthetic fixture rows.

## 17. End-to-End Flow

| Step through real FastAPI Gateway | Result |
|---|---|
| Register → Django → Node Notification mock | PASS |
| Verify OTP → Node User profile | PASS |
| Login → Python HS256 token | PASS |
| Python JWT → protected Node User /me | PASS |
| Auth projection excludes password/OTP | PASS |
| Cleanup only owned synthetic account/profile | PASS |

Frontend smoke là network/HTTP qua Nginx, không phải browser-rendered UI acceptance.

## 18. Database Safety

```text
Unexpected legacy schema changes:
NONE
```

Tám schema fingerprints và row counts khớp snapshot đầu Phase 2 sau E2E cleanup.
Legacy IDs/passwords không bị migrate. E2E tạo một account/profile synthetic, kiểm
tra profile slot trống trước OTP, xóa đúng ID + identity sở hữu; không reset AI.
Ba test schemas là empty clones được tạo riêng, không copy legacy accounts; sau
pytest chỉ fixtures thuộc các test schemas bị DELETE. Không TRUNCATE/drop baseline.
Snapshot không hash mọi business value; safety claim dựa vào operations/scope và
schema/count checks, không tuyên bố checksum toàn bộ data.

## 19. Files Created

32 files mới, đối chiếu snapshot trước Phase 2:

```text
api-gateway/app/proxy.py
api-gateway/tests/test_proxy.py
auth-service/authentication/exceptions.py
auth-service/authentication/models.py
auth-service/authentication/selectors.py
auth-service/authentication/serializers.py
auth-service/authentication/services/__init__.py
auth-service/authentication/services/clients.py
auth-service/authentication/services/login.py
auth-service/authentication/services/otp.py
auth-service/authentication/services/passwords.py
auth-service/authentication/services/registration.py
auth-service/authentication/services/tokens.py
auth-service/authentication/urls.py
auth-service/authentication/views.py
auth-service/tests/test_auth.py
contracts/auth/phase-2.json
docker-compose.phase2.rollback.yml
docker-compose.phase2.test.yml
docker-compose.phase2.yml
docs/migration/phase-2-files.md
docs/migration/phase-2-implementation-report.md
docs/migration/phase-2.md
integration-tests/phase2/conftest.py
integration-tests/phase2/pytest.ini
integration-tests/phase2/test_auth_parity.py
integration-tests/phase2/test_gateway_transport.py
tools/prepare_phase2_tests.py
tools/runtime/legacy-schema-guard.cjs
tools/runtime/node-reference-preload.cjs
tools/runtime/proxy-fixture.cjs
tools/verify_phase2_runtime.py
```

## 20. Files Modified

21 files Phase 1 được cập nhật:

```text
.env.python.example
api-gateway/.env.example
api-gateway/app/logging_config.py
api-gateway/app/main.py
api-gateway/app/middleware.py
api-gateway/app/settings.py
api-gateway/requirements.lock.txt
api-gateway/requirements.txt
api-gateway/tests/test_health.py
auth-service/.env.example
auth-service/common/logging.py
auth-service/common/middleware.py
auth-service/config/settings.py
auth-service/config/urls.py
auth-service/requirements.lock.txt
auth-service/requirements.txt
auth-service/tests/test_health.py
contracts/README.md
docker-compose.python.yml
requirements-dev.lock.txt
tools/verify_foundation.py
```

Node business/legacy Dockerfiles, baseline Compose, SQL/seeds và frontend giữ nguyên.

## 21. Git Status

PRE-EXISTING: HUONG_DAN_TRIEN_KHAI.md untracked, untouched.
PHASE 1: foundations/docs/contracts và .gitignore đang chưa commit được bảo toàn.
PHASE 2: files mới/modified liệt kê trong manifest theo hash snapshot trước phase.
Branch/HEAD giữ nguyên; không stage, commit hoặc push.

## 22. Known Issues

Nginx resolve DNS khi startup: sau Gateway recreate phải restart frontend. Lần
rerun đã phát hiện IP cũ được cấp cho test fixture; không sửa frontend, chỉ refresh
DNS bằng restart. Bare Bearer error envelope ban đầu khác Node đã được sửa theo
parity test. Real SMTP, browser UI interactions và toàn bộ realtime delivery chưa
được chứng nhận. Email mock là lựa chọn môi trường dev; debt Node vẫn tồn tại.

## 23. Phase 3 Readiness

Sẵn sàng cho Phase 3 — User + Category. 281 local tests, 35 integration tests,
Gateway/Auth Docker runtime, E2E Node token acceptance và DB safety checks đã pass.
Không còn blocker Phase 2; production caveats/security debt ở section 22 vẫn cần
được xử lý có chủ đích trong các phases phù hợp. Chưa implement Phase 3.

## 24. Suggested Commits

Chỉ đề xuất, chưa tạo:

```text
feat(gateway): migrate REST gateway to FastAPI
feat(auth): migrate authentication service to Django
test(auth): add Node Python authentication parity tests
test(gateway): add proxy contract tests
docs: document phase 2 migration and intentional divergences
```

Commands vận hành/test/cutover/rollback ở [phase-2.md](phase-2.md).
Evidence local ignored: .artifacts/phase2/*; không lưu passwords/OTPs/JWT trong report.
