# PHASE 1 IMPLEMENTATION REPORT

## 1. Summary

Đã triển khai Python foundation cho 10 services, Docker overlay và contract baseline.
Local verification pass 165 tests và 22/22 commands. **Phase 1 đạt Definition of
Done** sau khi Docker được khôi phục: 10 final images build được, 10 containers
healthy/ready, 9 Django checks trong Linux containers pass và 8 DB khớp snapshot
ban đầu. Đã chuẩn bị tài liệu Phase 2; chưa triển khai nghiệp vụ hoặc cutover.

## 2. Architecture

Python 3.12; gateway FastAPI/Uvicorn/httpx/pydantic-settings. Chín project Django
5.2/DRF/drf-spectacular độc lập, Gunicorn, cấu hình env; tám project kết nối MySQL
bằng mysqlclient. Notification chỉ là foundation cho email delivery, không có DB.
Health, readiness, request ID, JSON logs, CORS allowlist và OpenAPI đã có.
Không có business models/migrations, proxy thực, JWT business logic, Redis, Celery,
Channels, Conversation model, cloud deployment hay CI/CD.

## 3. Files Created

Danh sách đầy đủ tại [phase-1-files.md](phase-1-files.md).

- Mỗi Django service: manage.py; config/settings/urls/wsgi/asgi; common health,
  middleware, logging; business app skeleton; tests; pytest.ini; requirements và
  runtime lock; .env.example; Dockerfile.python và Dockerfile.python.dockerignore.
- Gateway: app/settings/middleware/logging_config/main; tests; requirements/lock;
  pytest.ini; .env.example; Dockerfile.python và Dockerfile.python.dockerignore.
- Root: docker-compose.python.yml, .env.python.example, pyproject.toml,
  requirements-dev.txt, requirements-dev.lock.txt.
- contracts/, contract-tests/, tools/lock_foundation.py, tools/verify_foundation.py,
  tools/verify_runtime.py, docs/migration/.

## 4. Files Modified

Chỉ `.gitignore`: bỏ qua venv/cache/artifacts/local Python env, giữ .env.example
reviewable. SHA-256 đối chiếu 157 file baseline xác nhận 156 file còn lại nguyên vẹn.

## 5. Node/Python Coexistence

Node giữ tên canonical, code và host ports hiện tại. Python dùng tên `*-python`,
chỉ ports nội bộ. Compose merged cho phép cùng tồn tại, không override Node.
Hiện 10 Python foundations và 8 MySQL baseline containers đang chạy. Không start
Node vì startup có thể chạy Sequelize sync alter. Compose hỗ trợ coexistence,
nhưng chưa xác nhận parity nghiệp vụ Node/Python đồng thời.

## 6. Docker Strategy

Overlay additive dùng cùng project/network/DB volumes baseline; 19 service
definitions cũ được so sánh normalized và giữ nguyên, thêm đúng 10 services.
Python không publish host ports, không fixed container_name. Post/Review mount
shared_uploads read-only. Dockerfiles chạy non-root; MySQL build dependencies nằm
ở build stage. Không startup migrate hoặc DB wait loop vô hạn.
Lệnh setup/build/start và cách dùng env tại [phase-1.md](phase-1.md).

## 7. Service Matrix

Health/Ready trong bảng là **runtime Docker**, không phải kết quả unit test.

| Service | Target Framework | Port | Database | Health | Ready |
|---|---|---:|---|---|---|
| api-gateway | FastAPI | 3000 | None | PASS | PASS |
| auth-service | Django/DRF | 3001 | auth_db | PASS | PASS |
| user-service | Django/DRF | 3002 | user_db | PASS | PASS |
| post-service | Django/DRF | 3003 | post_db | PASS | PASS |
| category-service | Django/DRF | 3004 | category_db | PASS | PASS |
| message-service | Django/DRF | 3005 | message_db | PASS | PASS |
| notification-service | Django/DRF | 3006 | None | PASS | PASS |
| review-service | Django/DRF | 3007 | review_db | PASS | PASS |
| search-service | Django/DRF | 3008 | search_db | PASS | PASS |
| favorite-service | Django/DRF | 3009 | favorite_db | PASS | PASS |

Unit tests health/ready pass ở cả 10 services. DB-backed readiness dùng SELECT 1,
200 khi kết nối được, 503 khi không kết nối được. Gateway/Notification readiness
không truy cập DB hoặc gửi email.

## 8. Database Safety

```text
Legacy schema changes performed:
NONE
```

Không migrate/makemigrations/flush, seed/import, ALTER/DROP/TRUNCATE, Sequelize
sync, down -v hoặc volume deletion. Đọc metadata và row counts trước Python
startup; snapshot lưu ở ignored .artifacts/phase1/db-before.json. Tám DB ban đầu
SELECT 1 thành công; không có Django system tables. Favorite physical table là
favorites, MySQL case mode=1; live Review có imageUrl, seed thiếu column này.
Đối chiếu snapshot trước recovered startup và sau startup **PASS**: cả tám schema
fingerprints và row counts giữ nguyên.
[Table mapping](table-mapping.md) ghi tên và constraints cho migration sau.

## 9. Contract Baseline

37 route declarations từ Node: method, gateway/service paths, aliases, auth,
request, success/error status và shapes, evidence source. Giữ prefixes không có
/api, routes admin/uploads/socket, camelCase, numeric IDs và envelopes riêng.
Có JWT HS256/claims/TTL/Bearer contract, bcrypt $2a$/$2b$ test plan, Socket.IO
events/rooms, post compatibility và synthetic fixtures. Comparator chuẩn bị so
status, JSON keys/types, headers; chưa thực hiện business parity qua network.
GET /messages/notifications bị shadow và OTP lỗi trả 500 được ghi đúng baseline.

## 10. Verification Results

| Verification | Result |
|---|---|
| Ruff check / format check | PASS |
| 9 manage.py check | PASS |
| Pytest | PASS: 165 tests (144 Django + 7 gateway + 14 contracts) |
| pip check | PASS |
| Original + merged Compose config | PASS |
| Original service definitions preserved | PASS: 19/19 |
| Initial Docker build | PASS: 10/10 images, trước refinements cuối |
| Final-source rebuild | PASS: 10/10 sau Docker recovery; Review rebuild không cache để sửa cached image thiếu appuser |
| Docker startup | PASS: 10/10 foundations running và Docker healthy |
| Docker runtime verifier | PASS |
| 10 health / 10 readiness thực tế | PASS: HTTP 200; 8 DB-backed services report connected |
| Final DB comparison | PASS: 8/8 schema fingerprints và row counts giữ nguyên |
| Linux container Django checks | PASS: 9/9 |
| Peer DNS / OpenAPI / Swagger | PASS: 10/10 |

Đã đọc lỗi và thử phục hồi engine bằng Desktop restart/stop, targeted WSL
termination và restart đúng executables Docker. Log VM xác nhận dockerd signal 7
và input/output error trong lần kiểm chứng đầu. Sau khi người dùng khôi phục engine,
đã rebuild/start/check thành công. Review cached image thiếu appuser được sửa bằng
rebuild riêng không cache; UID 10001 được kiểm tra. Không reset/prune/xóa dữ liệu.
Chi tiết, commands và bằng chứng tại [phase-1-verification.md](phase-1-verification.md).

## 11. Existing Issues

Security debt Node, frontend contract mismatches, Socket.IO rooms, OTP error mapping,
search synchronization, proxy hooks và Review seed/live mismatch được ghi tại
[security-debt.md](security-debt.md), [compatibility-notes.md](compatibility-notes.md).
Không sửa các business issues trong Phase 1. Gateway tests có một warning upstream
Starlette TestClient/httpx; tests pass. Docker engine outage đã được khôi phục và
Review cache issue đã xử lý; không còn blocker runtime Phase 1.

## 12. Git Status

```text
PRE-EXISTING
?? HUONG_DAN_TRIEN_KHAI.md

PHASE 1
 M .gitignore
?? Python foundations / Compose overlay / contracts / tests / tooling / docs
```

HUONG_DAN_TRIEN_KHAI.md không edit/add/commit/reset. Không staging hoặc commit.
Branch và HEAD baseline giữ nguyên. Local venv/artifacts/cache được ignore.

## 13. Phase 2 Readiness

Cấu trúc gateway và Auth, env URLs, DB mapping, dependency locks, logging,
health/ready/OpenAPI và contract scaffolding sẵn sàng. Gate runtime Phase 1 đã pass.
Kế hoạch triển khai và isolated tests ở [phase-2-readiness.md](phase-2-readiness.md).
JWT/bcrypt interop, Auth business logic, proxy migration và cutover thuộc Phase 2;
chưa implement hoặc đổi traffic trong lượt chuẩn bị này.

## 14. Suggested Commits

Chỉ đề xuất; chưa tạo commits:

```text
chore: add Python microservices foundation
chore(docker): add Python migration environment
test: add microservices health and readiness checks
docs: add migration contract baseline
```

Chỉ stage files Phase 1 theo manifest; tránh git add . vì có file pre-existing.
