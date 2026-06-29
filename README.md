# Đồ Cũ - Microservices Architecture

Dự án "Đồ Cũ" đã được tái cấu trúc từ Monolith sang kiến trúc Microservices để đảm bảo khả năng mở rộng (scalability) và dễ dàng bảo trì.

## 🏗 Cấu Trúc Hệ Thống (9 Microservices)

Toàn bộ hệ thống được đặt phía sau một **API Gateway** (Port 3000). Các request từ Frontend sẽ gọi tới Gateway và được định tuyến tự động đến các service tương ứng.

1. `api-gateway`: Cửa ngõ API, định tuyến request và WebSockets (Port 3000).
2. `auth-service`: Quản lý xác thực (JWT, Login/Register) (Database: `auth-db`).
3. `user-service`: Quản lý hồ sơ người dùng (Database: `user-db`).
4. `post-service`: Quản lý bài đăng bán và upload hình ảnh (Database: `post-db`).
5. `category-service`: Quản lý danh mục (Database: `category-db`).
6. `message-service`: Chat thời gian thực qua Socket.io (Database: `message-db`).
7. `notification-service`: Gửi Email (Nodemailer).
8. `review-service`: Quản lý đánh giá người dùng (Database: `review-db`).
9. `search-service`: Tìm kiếm và lọc sản phẩm (Database: `search-db`).

- `do-cu-frontend`: Giao diện React/Vite (Port 80).

## 🚀 Hướng Dẫn Cài Đặt & Chạy Dự Án

### Yêu cầu hệ thống
- **Docker Desktop** đã cài đặt và **đang chạy** (tải tại: https://www.docker.com/products/docker-desktop)
- **Không cần** cài thêm Node.js, MySQL hay bất kỳ phần mềm nào khác — Docker lo tất cả.
- RAM khuyến nghị: **8GB trở lên** (hệ thống chạy 17 container cùng lúc).

### Bước 1: Giải nén
Giải nén file `.zip` vào một thư mục bất kỳ trên máy.

### Bước 2: Mở Terminal
Mở **PowerShell** hoặc **Command Prompt** và di chuyển vào thư mục dự án:
```bash
cd đường-dẫn-tới-thư-mục\KienTrucPM
```

### Bước 3: Build và Khởi Động Hệ Thống
```bash
docker-compose up --build -d
```
- Lần đầu tiên sẽ mất khoảng **3 - 10 phút** (tuỳ tốc độ mạng) để tải image và build.
- Tham số `-d` giúp hệ thống chạy ngầm ở chế độ background.
- Đợi đến khi terminal hiện toàn bộ `Started` là xong.

### Bước 4: Import Dữ Liệu Mẫu
Đợi khoảng **30 giây** sau khi build xong (để Database khởi tạo), rồi chạy:

```powershell
powershell -ExecutionPolicy Bypass -File migrate.ps1
```

Lệnh này sẽ import dữ liệu mẫu (tài khoản, bài đăng, danh mục, tin nhắn) từ file `docu_db (1).sql` vào các Database Microservices.

### Bước 5: Đồng Bộ Dữ Liệu Tìm Kiếm
```bash
docker exec post-service node sync-all.js
```
Lệnh này đồng bộ tất cả bài đăng đã duyệt vào Search Service để chức năng tìm kiếm hoạt động.

### Bước 6: Truy Cập Website
- **Frontend (Giao diện web):** http://localhost
- **API Gateway:** http://localhost:3000

**Tài khoản mẫu** (nếu có trong dữ liệu):
- Đăng nhập tại giao diện web, tài khoản và mật khẩu tuỳ thuộc vào dữ liệu trong file SQL.

---

## 🛠 Các Lệnh Docker Hữu Ích

**1. Xem trạng thái tất cả container:**
```bash
docker-compose ps
```

**2. Xem logs (lỗi hoặc thông báo) của toàn bộ hệ thống:**
```bash
docker-compose logs -f
```

**3. Xem logs của 1 service cụ thể (ví dụ: api-gateway):**
```bash
docker logs api-gateway -f
```

**4. Tắt hệ thống:**
```bash
docker-compose down
```

**5. Tắt hệ thống và xóa sạch toàn bộ Database (Reset dữ liệu):**
```bash
docker-compose down -v
```

**6. Khởi động lại sau khi đã build (nhanh hơn):**
```bash
docker-compose up -d
```

---

## 🔧 Lưu Ý Quan Trọng

### Cấu hình Frontend
Frontend đã được cấu hình sẵn trỏ về API Gateway. File `.env`:
```
VITE_API_URL=http://localhost:3000
```
Mọi API đều gọi qua cổng `3000` này.

### Xử lý sự cố thường gặp
| Lỗi | Nguyên nhân | Cách sửa |
|---|---|---|
| `port is already allocated` | Cổng đã bị ứng dụng khác chiếm | Tắt ứng dụng đang dùng cổng đó, hoặc đổi port trong `docker-compose.yml` |
| `migrate.ps1 cannot be loaded` | PowerShell chặn script | Chạy: `powershell -ExecutionPolicy Bypass -File migrate.ps1` |
| Database trống sau migrate | Container DB chưa kịp khởi tạo | Đợi 30s rồi chạy lại `migrate.ps1` |
| Tìm kiếm không có kết quả | Chưa sync dữ liệu Search | Chạy: `docker exec post-service node sync-all.js` |
## 📦 Phien Ban Release v1.0.0
- Tich hop toan bo cac microservices.
- Giao dien nguoi dung hoan thien.
- Ho tro chat thoi gian thuc va thong bao.


### ⚠️ Hotfix v1.0.1
- Va loi phan quyen admin truy cap trang duyet tin.

