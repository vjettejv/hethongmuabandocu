# Chợ Đồ Cũ — Tổng quan dự án và nội dung tham khảo cho CV

Bản tổng hợp hệ thống hiện tại, cập nhật ngày 07/10/2026. README mô tả backend Python;
các báo cáo migration giữ thông tin lịch sử của backend Node.js trước khi chuyển đổi.

## Mục tiêu

Ứng dụng web mua bán đồ cũ: người dùng đăng tin kèm ảnh, tìm kiếm sản phẩm, lưu yêu
thích, trao đổi với người bán và đánh giá người dùng. Giao diện quản trị hỗ trợ duyệt
hoặc từ chối tin đăng trước khi tin xuất hiện trên trang chủ/tìm kiếm.

## Công nghệ và kiến trúc

- Frontend: React 18, Vite, React Router, Axios, Socket.IO client, CSS.
- API Gateway: FastAPI, HTTPX; định tuyến HTTP và proxy kết nối Socket.IO/WebSocket.
- Backend nghiệp vụ: Python, Django, Django REST Framework, Django ORM.
- Xác thực: JWT; đăng ký và xác minh tài khoản bằng OTP.
- Chat và thông báo realtime: python-socketio, ASGI/Uvicorn.
- Dữ liệu: 8 database MySQL riêng theo dịch vụ; upload ảnh dùng volume chung.
- Vận hành local: Docker, Docker Compose, Nginx; health/readiness endpoints.
- Kiểm thử: pytest, pytest-django, contract/parity tests, integration tests;
  frontend có kiểm thử hợp đồng dữ liệu bằng Node test runner.

Có **9 dịch vụ nghiệp vụ Django + 1 FastAPI Gateway**, tổng cộng **10 backend**.
Compose canonical gồm 10 backend, 8 database và 1 frontend/Nginx, tổng cộng 19 container.

| Dịch vụ | Trách nhiệm |
|---|---|
| Auth | Đăng ký, OTP, đăng nhập, JWT |
| User | Hồ sơ người dùng |
| Post | Tin đăng, upload ảnh, thao tác duyệt/từ chối |
| Category | Danh mục sản phẩm |
| Favorite | Lưu/bỏ yêu thích |
| Review | Đánh giá người dùng |
| Search | Tìm kiếm, lọc sản phẩm từ dữ liệu được đồng bộ |
| Message | Hội thoại, tin nhắn, thông báo trong ứng dụng và Socket.IO |
| Notification | Gửi email qua SMTP hoặc chế độ mock local |
| API Gateway | Cổng truy cập HTTP và Socket.IO cho frontend |

Luồng truy cập: **React → Nginx → FastAPI Gateway → Django service → MySQL**.
Các dịch vụ trao đổi qua HTTP; chat realtime qua Socket.IO. Search hiện dùng MySQL,
không dùng Elasticsearch, Redis, Kafka hoặc RabbitMQ trong stack canonical.

## Công việc kỹ thuật nổi bật trong repository

- Chuyển backend Node.js sang FastAPI/Django, giữ tương thích API, schema MySQL,
  định dạng dữ liệu, upload và Socket.IO với frontend hiện có.
- Tách trách nhiệm và database theo dịch vụ; quản lý các kết nối qua API Gateway.
- Đóng gói hệ thống bằng Docker Compose, cấu hình Nginx, health/readiness và logging.
- Kiểm thử hợp đồng API, so sánh hành vi backend cũ/mới, kiểm thử tích hợp và khôi phục.
- Hoàn thiện các luồng frontend: phiên đăng nhập, hồ sơ, đăng tin, tin của tôi,
  yêu thích, chat và quản trị tin đăng.
- Chuẩn hóa trạng thái tin **pending → approved / rejected**; chuyển dữ liệu legacy
  bằng migration có journal, kiểm tra bảo toàn dữ liệu và rollback có điều kiện.
- Cấu hình GitHub Actions cho kiểm tra Python/frontend, build Docker và integration
  trên stack riêng; workflow GHCR cho 11 image, manual mặc định không publish.

Đây là dự án đã chạy và kiểm thử local. CI/CD đã được cấu hình, chưa chạy workflow
trên GitHub hoặc publish image trong Phase 8. Không xác nhận triển khai production,
lượng người dùng thực tế, benchmark tải hay hoàn thiện toàn bộ phân quyền.

## Mẫu nội dung CV

**Chợ Đồ Cũ — Ứng dụng mua bán đồ cũ theo kiến trúc Microservices**

**Tech stack:** Python, Django REST Framework, FastAPI, React, MySQL, Socket.IO,
Docker Compose, Nginx, pytest.

Chọn các ý phù hợp với phần việc thực tế bạn đảm nhiệm:

- Phát triển ứng dụng mua bán đồ cũ với các chức năng xác thực JWT/OTP, đăng tin kèm
  ảnh, tìm kiếm, yêu thích, đánh giá và quản trị duyệt tin.
- Triển khai kiến trúc gồm 9 dịch vụ Django và FastAPI API Gateway, sử dụng 8 database
  MySQL; tích hợp chat và thông báo thời gian thực bằng Socket.IO.
- Chuyển backend Node.js sang Python, duy trì tương thích API và dữ liệu; đóng gói hệ
  thống bằng Docker Compose/Nginx và kiểm thử hợp đồng API, luồng tích hợp bằng pytest.
- Cấu hình pipeline GitHub Actions kiểm tra mã nguồn, build frontend/Docker và chạy
  integration trên tài nguyên độc lập; thiết lập workflow phát hành image qua GHCR.

Điền thêm thời gian, vai trò, quy mô nhóm và link GitHub/demo theo thông tin thực tế.
Không dùng toàn bộ các ý như thành tích cá nhân nếu đó là phần việc của thành viên khác.

## Tài liệu chi tiết

- [Hướng dẫn hiện tại](../README.md)
- [Kiến trúc hệ thống](architecture.md)
- [CI/CD và giới hạn xác minh](ci-cd.md)
- [Báo cáo Phase 8](migration/phase-8-report.md)
- [Kiến trúc và báo cáo tích hợp Phase 7](migration/phase-7-implementation-report.md)
- [Vận hành và kiểm thử](migration/phase-7-runbook.md)
- [Rà soát frontend](migration/frontend-audit-report.md)
- [Chuẩn hóa trạng thái backend và dữ liệu](migration/post-status-normalization.md)
