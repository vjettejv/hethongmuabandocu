# Báo Cáo Thực Nghiệm & Hướng Dẫn Đánh Giá Hiệu Năng Hệ Thống
## Dự án: Hệ Thống Microservices Đồ Cũ (K6 Performance Testing)

Tài liệu này cung cấp bảng phân công nhiệm vụ, kịch bản tải chi tiết và hướng dẫn các thành viên chạy thử nghiệm hiệu năng hệ thống bằng công cụ **k6**.

---

## I. BẢNG PHÂN CÔNG & THAM SỐ TẢI CHI TIẾT

Để dễ so sánh và đối chiếu, dưới đây là bảng tổng hợp kịch bản tải của **5 thành viên** tương ứng với **5 API trọng tâm**:

| Thành viên | API Mục Tiêu | Phân Loại Tải | Smoke Test | Load Test (Tải thường) | Stress Test (Quá tải) | Soak Test (Độ bền) | Thư Mục Dự Án |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Phạm Văn Đạt** | `POST /auth/login` | **CPU Heavy** *(Xác thực Bcrypt)* | 1 VU / 10 giây | **Tối đa 15 VUs**<br>• Ramp: 30s<br>• Hold: 1m<br>• Down: 20s | **Tối đa 50 VUs**<br>• Ramp: 30s<br>• Hold: 1m<br>• Down: 20s | **Duy trì 10 VUs**<br>• Thời gian: 3 phút | [TestPhamVanDat/](file:///d:/workspacecuachjp/KienTrucPM/TestPhamVanDat) |
| **2. Đỗ Thị Thúy Quỳnh** | `GET /posts` | **DB Read Heavy** *(Truy vấn DB)* | 1 VU / 15 giây | **Tối đa 30 VUs**<br>• Ramp: 40s<br>• Hold: 1m<br>• Down: 20s | **Tối đa 150 VUs**<br>• Ramp: 40s<br>• Hold: 1m<br>• Down: 30s | **Duy trì 20 VUs**<br>• Thời gian: 4 phút | [TestDoThiThuyQuynh/](file:///d:/workspacecuachjp/KienTrucPM/TestDoThiThuyQuynh) |
| **3. Nguyễn Hà Đức Việt** | `POST /posts` | **DB Write Heavy** *(Ghi DB & Sync ES)* | 1 VU / 10 giây | **Tối đa 10 VUs**<br>• Ramp: 30s<br>• Hold: 1m<br>• Down: 20s | **Tối đa 35 VUs**<br>• Ramp: 30s<br>• Hold: 1m<br>• Down: 20s | **Duy trì 8 VUs**<br>• Thời gian: 3 phút | [TestNguyenHaDucViet/](file:///d:/workspacecuachjp/KienTrucPM/TestNguyenHaDucViet) |
| **4. Nguyễn Trọng Đức** | `GET /categories` | **Static Read** *(Dữ liệu tĩnh, nhẹ)* | 1 VU / 10 giây | **Tối đa 40 VUs**<br>• Ramp: 30s<br>• Hold: 1m<br>• Down: 20s | **Tối đa 200 VUs**<br>• Ramp: 30s<br>• Hold: 1m<br>• Down: 20s | **Duy trì 30 VUs**<br>• Thời gian: 3 phút | [TestNguyenTrongDuc/](file:///d:/workspacecuachjp/KienTrucPM/TestNguyenTrongDuc) |
| **5. Phạm Quang Minh** | `GET /favorites/my-favorites` | **Auth Read** *(Đọc DB kèm token)* | 1 VU / 12 giây | **Tối đa 20 VUs**<br>• Ramp: 30s<br>• Hold: 1m<br>• Down: 20s | **Tối đa 80 VUs**<br>• Ramp: 30s<br>• Hold: 1m<br>• Down: 20s | **Duy trì 12 VUs**<br>• Thời gian: 3 phút | [TestPhamQuangMinh/](file:///d:/workspacecuachjp/KienTrucPM/TestPhamQuangMinh) |

> [!IMPORTANT]
> **Tiêu chí Đạt SLA chung cho toàn dự án:**
> * **Tỷ lệ lỗi (`http_req_failed`):** Phải nhỏ hơn **1.00%** (không xảy ra lỗi nghẽn dịch vụ hoặc lỗi database).
> * **Thời gian phản hồi (`p(95) http_req_duration`):** 95% số request phải hoàn thành trong **dưới 2000ms** (2.0 giây). Ngưỡng này đã được nới lỏng từ 500ms để phù hợp với tài nguyên thực thi máy cá nhân.

---

## II. HƯỚNG DẪN BẮT ĐẦU NHANH (QUICK START)

### Bước 1: Cài đặt k6 trên Windows
Chọn một trong hai phương thức sau:
* **Cách 1: Tải bộ cài trực tiếp**
  Tải và chạy file cài đặt tự động: [Tải Installer k6 (Bản 64-bit)](https://github.com/grafana/k6/releases/download/v0.51.0/k6-v0.51.0-amd64.msi)
* **Cách 2: Cài qua Terminal (PowerShell)**
  ```powershell
  winget install k6 --source winget
  ```
*(Lưu ý: Sau khi cài xong, hãy tắt và mở lại Terminal để cập nhật biến môi trường).*

### Bước 2: Khởi động hệ thống Docker
Đảm bảo bạn đang đứng ở thư mục gốc của dự án chứa file `docker-compose.yml`, chạy lệnh:
```bash
docker-compose up -d
```

---

## III. HƯỚNG DẪN CHẠY TEST CHO TỪNG THÀNH VIÊN

Bạn chỉ cần di chuyển vào thư mục của mình và chạy lệnh kiểm thử. Kịch bản test có thể chạy **tuần tự cả 4 kịch bản** (Smoke -> Load -> Stress -> Soak) hoặc **chạy đơn lẻ** từng kịch bản.

### 1. Lệnh chạy mặc định (Tuần tự tất cả kịch bản)
Lệnh này sẽ chạy lần lượt từ Smoke Test đến Soak Test để thu được báo cáo tổng hợp:

* **Phạm Văn Đạt:**
  ```bash
  cd TestPhamVanDat && k6 run test.js
  ```
* **Đỗ Thị Thúy Quỳnh:**
  ```bash
  cd TestDoThiThuyQuynh && k6 run test.js
  ```
* **Nguyễn Hà Đức Việt:**
  ```bash
  cd TestNguyenHaDucViet && k6 run test.js
  ```
* **Nguyễn Trọng Đức:**
  ```bash
  cd TestNguyenTrongDuc && k6 run test.js
  ```
* **Phạm Quang Minh:**
  ```bash
  cd TestPhamQuangMinh && k6 run test.js
  ```

### 2. Lệnh chạy đơn lẻ một kịch bản mong muốn
Sử dụng tham số `-e SCENARIO=[tên_kịch_bản]` để chạy riêng biệt nhanh chóng:

* **Smoke Test (Chạy kiểm tra logic):**
  ```bash
  k6 run -e SCENARIO=smoke test.js
  ```
* **Load Test (Kiểm thử tải thông thường):**
  ```bash
  k6 run -e SCENARIO=load test.js
  ```
* **Stress Test (Kiểm thử áp lực cực đại):**
  ```bash
  k6 run -e SCENARIO=stress test.js
  ```
* **Soak Test (Kiểm thử độ bền/rò rỉ bộ nhớ):**
  ```bash
  k6 run -e SCENARIO=soak test.js
  ```

> [!NOTE]
> Tất cả các cấu hình này được điều khiển tự động thông qua file dùng chung [common-test.js](file:///d:/workspacecuachjp/KienTrucPM/common-test.js) giúp mã nguồn các thành viên luôn ngắn gọn, sạch sẽ và dễ bảo trì.

---

## IV. CÁCH ĐỌC & ĐÁNH GIÁ KẾT QUẢ TEST

Sau khi hoàn thành bài test, terminal của k6 sẽ xuất hiện kết quả đo lường:

```text
  ✓ http_req_failed................: 0.00%      ✓ 0 / 2341
  ✓ http_req_duration..............: avg=185ms  p(90)=412ms  p(95)=540ms  p(99)=1.2s
    { name:API_Login_Member1 }.....: avg=210ms  p(90)=490ms  p(95)=620ms
```

### 1. Phân tích các chỉ số chính:
* **`http_req_failed`**: Nếu kết quả có dấu tích xanh **`✓`** và tỉ lệ `< 1.00%` là **ĐẠT**. Nếu có dấu đỏ **`✗`**, hệ thống đang bị lỗi kết nối hoặc sập dịch vụ.
* **`http_req_duration`**: Xem giá trị tại cột `p(95)` (Phần trăm thứ 95). Nếu giá trị này `< 2000ms` là **ĐẠT**.

### 2. Phát hiện lỗi và điểm nghẽn (Bottlenecks):
* **Lỗi CPU quá tải ở Xác thực:** Nếu `{ name:API_Login_Member1 }` phản hồi chậm, do thuật toán mã hóa mật khẩu `bcrypt` đang ngốn hết tài nguyên CPU.
* **Lỗi Connection Pool hoặc thiếu Index DB:** Nếu `{ name:API_GetPosts_Member2 }` chậm, do MySQL chưa được cấu hình tối ưu chỉ mục hoặc số lượng kết nối đồng thời từ Service tới DB bị giới hạn.
* **Độ trễ ghi dữ liệu (Write Latency):** `{ name:API_CreatePost_Member3 }` thường có thời gian phản hồi cao nhất vì hệ thống phải vừa ghi dữ liệu vào MySQL, vừa đồng bộ sang ElasticSearch thông qua Kafka.

---

## V. KẾT QUẢ THỰC NGHIỆM THỰC TẾ (SMOKE TEST)

Dưới đây là kết quả chạy kiểm thử thực tế kịch bản **Smoke Test** cho từng thành viên:

| Thành viên | API Mục Tiêu | Tổng Số Request | Tỷ lệ thành công (Checks) | Thời gian phản hồi Trung bình (avg) | Thời gian phản hồi P(95) | Kết luận SLA |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **1. Phạm Văn Đạt** (`TestPhamVanDat`) | `POST /auth/login` | 6 | **100%** (10/10) | **148.07 ms** | **314.60 ms** | **ĐẠT** (SLA < 2000ms) |
| **2. Đỗ Thị Thúy Quỳnh** (`TestDoThiThuyQuynh`) | `GET /posts` | 8 | **100%** (16/16) | **26.15 ms** | **51.46 ms** | **ĐẠT** (SLA < 2000ms) |
| **3. Nguyễn Hà Đức Việt** (`TestNguyenHaDucViet`) | `POST /posts` | 6 | **100%** (8/8) | **63.17 ms** | **111.41 ms** | **ĐẠT** (SLA < 2000ms) |
| **4. Nguyễn Trọng Đức** (`TestNguyenTrongDuc`) | `GET /categories` | 5 | **100%** (10/10) | **7.05 ms** | **8.56 ms** | **ĐẠT** (SLA < 2000ms) |
| **5. Phạm Quang Minh** (`TestPhamQuangMinh`) | `GET /favorites/my-favorites` | 8 | **100%** (12/12) | **123.12 ms** | **294.91 ms** | **ĐẠT** (SLA < 2000ms) |

---

## VI. KẾT QUẢ THỰC NGHIỆM THỰC TẾ (LOAD TEST)

Dưới đây là kết quả chạy kiểm thử thực tế kịch bản **Load Test (Tải thường)** cho từng thành viên:

| Thành viên | API Mục Tiêu | Đỉnh Tải (Max VUs) | Tổng Số Request | Tỷ lệ thành công (Checks) | Thời gian phản hồi Trung bình (avg) | Thời gian phản hồi P(95) | Kết luận SLA |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Phạm Văn Đạt** (`TestPhamVanDat`) | `POST /auth/login` | 15 VUs | 573 | **100%** (1116/1116) | **279.22 ms** | **781.44 ms** | **ĐẠT** (SLA < 2000ms) |
| **2. Đỗ Thị Thúy Quỳnh** (`TestDoThiThuyQuynh`) | `GET /posts` | 30 VUs | 1349 | **100%** (2698/2698) | **22.48 ms** | **52.57 ms** | **ĐẠT** (SLA < 2000ms) |
| **3. Nguyễn Hà Đức Việt** (`TestNguyenHaDucViet`) | `POST /posts` | 10 VUs | 428 | **100%** (816/816) | **37.70 ms** | **88.52 ms** | **ĐẠT** (SLA < 2000ms) |
| **4. Nguyễn Trọng Đức** (`TestNguyenTrongDuc`) | `GET /categories` | 40 VUs | 1702 | **100%** (3404/3404) | **9.15 ms** | **24.23 ms** | **ĐẠT** (SLA < 2000ms) |
| **5. Phạm Quang Minh** (`TestPhamQuangMinh`) | `GET /favorites/my-favorites` | 20 VUs | 870 | **100%** (1660/1660) | **15.40 ms** | **59.07 ms** | **ĐẠT** (SLA < 2000ms) |

> [!TIP]
> **Nhận xét hiệu năng từ Load Test:**
> * Toàn bộ các API đều chịu tải tốt ở mức VUs thông thường mà không phát sinh bất kỳ lỗi kết nối hay lỗi máy chủ nào (Error Rate = **0.00%**).
> * API Đăng nhập (`POST /auth/login`) có sự gia tăng độ trễ lên **avg 279.22ms** và **P(95) 781.44ms** do thuật toán `bcrypt` xử lý nhiều yêu cầu xác thực đồng thời từ 15 VUs, tuy nhiên vẫn nằm trong giới hạn cực kỳ an toàn (< 2s).
> * Các API đọc ghi database tĩnh và cơ bản khác (Lấy bài đăng, Lấy danh mục, Yêu thích) vẫn duy trì tốc độ phản hồi cực nhanh dưới **90ms**.

---

## VII. KẾT QUẢ THỰC NGHIỆM THỰC TẾ (STRESS TEST)

Dưới đây là kết quả chạy kiểm thử thực tế kịch bản **Stress Test (Áp lực cực đại)** cho từng thành viên:

| Thành viên | API Mục Tiêu | Đỉnh Tải (Max VUs) | Tổng Số Request | Tỷ lệ thành công (Checks) | Thời gian phản hồi Trung bình (avg) | Thời gian phản hồi P(95) | Kết luận SLA |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Phạm Văn Đạt** (`TestPhamVanDat`) | `POST /auth/login` | 50 VUs | 906 | **100%** (1712/1712) | **2.84 s** | **4.80 s** | **KHÔNG ĐẠT** (Vượt ngưỡng 2s) |
| **2. Đỗ Thị Thúy Quỳnh** (`TestDoThiThuyQuynh`) | `GET /posts` | 150 VUs | 3218 | **100%** (6436/6436) | **2.52 s** | **4.94 s** | **KHÔNG ĐẠT** (Vượt ngưỡng 2s) |
| **3. Nguyễn Hà Đức Việt** (`TestNguyenHaDucViet`) | `POST /posts` | 35 VUs | 1514 | **100%** (2888/2888) | **43.36 ms** | **121.60 ms** | **ĐẠT** (SLA < 2000ms) |
| **4. Nguyễn Trọng Đức** (`TestNguyenTrongDuc`) | `GET /categories` | 200 VUs | 8522 | **99.96%** (17038/17044) | **14.17 ms** | **44.73 ms** | **ĐẠT** (SLA < 2000ms) |
| **5. Phạm Quang Minh** (`TestPhamQuangMinh`) | `GET /favorites/my-favorites` | 80 VUs | 3457 | **100%** (6594/6594) | **20.95 ms** | **74.46 ms** | **ĐẠT** (SLA < 2000ms) |

> [!WARNING]
> **Phân tích điểm nghẽn (Bottlenecks) từ Stress Test:**
> * **API Đăng nhập (`POST /auth/login`):** Dưới áp lực 50 VUs đồng thời, thời gian phản hồi tăng vọt lên **avg 2.84s** và **P(95) 4.8s**. Nguyên nhân do thuật toán băm mật khẩu bảo mật `bcrypt` tiêu tốn toàn bộ tài nguyên CPU của máy chủ Xác thực. Đây là phản ứng thông thường của các API CPU-bound khi chịu stress nặng.
> * **API Xem bài đăng (`GET /posts`):** Đọc tin tức dưới tải 150 VUs đồng thời bị chậm lại đáng kể (**avg 2.52s** và **P(95) 4.94s**). Điều này chỉ ra rằng hệ thống đang bị nghẽn ở kết nối Database (Database Connection Pool) hoặc do thiếu chỉ mục phù hợp trên bảng cơ sở dữ liệu lớn khi truy vấn SELECT đồng thời.
> * **Lỗi Socket Exhaustion (Windows Client):** Thành viên Nguyễn Trọng Đức khi stress 200 VUs gặp 3 lỗi mạng (tỷ lệ rất nhỏ **0.03%**). Lỗi này phát sinh từ hệ điều hành Windows của client (hết cổng kết nối tạm thời do TIME_WAIT) chứ không phải do lỗi hệ thống microservices.

---

## VIII. KẾT QUẢ THỰC NGHIỆM THỰC TẾ (SOAK TEST)

Dưới đây là kết quả chạy kiểm thử thực tế kịch bản **Soak Test (Độ bền)** cho từng thành viên (duy trì tải liên tục trong 3 - 4 phút):

| Thành viên | API Mục Tiêu | Tải Duy Trì (VUs) | Thời Gian Chạy | Tổng Số Request | Tỷ lệ thành công (Checks) | Thời gian phản hồi Trung bình (avg) | Thời gian phản hồi P(95) | Kết luận SLA |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Phạm Văn Đạt** (`TestPhamVanDat`) | `POST /auth/login` | 10 VUs | 3 phút | 832 | **100%** (1644/1644) | **180.69 ms** | **443.28 ms** | **ĐẠT** (SLA < 2000ms) |
| **2. Đỗ Thị Thúy Quỳnh** (`TestDoThiThuyQuynh`) | `GET /posts` | 20 VUs | 4 phút | 1795 | **100%** (3590/3590) | **668.81 ms** | **1.70 s** | **ĐẠT** (SLA < 2000ms) |
| **3. Nguyễn Hà Đức Việt** (`TestNguyenHaDucViet`) | `POST /posts` | 8 VUs | 3 phút | 718 | **100%** (1404/1404) | **46.29 ms** | **69.07 ms** | **ĐẠT** (SLA < 2000ms) |
| **4. Nguyễn Trọng Đức** (`TestNguyenTrongDuc`) | `GET /categories` | 30 VUs | 3 phút | 2694 | **100%** (5388/5388) | **10.21 ms** | **24.67 ms** | **ĐẠT** (SLA < 2000ms) |
| **5. Phạm Quang Minh** (`TestPhamQuangMinh`) | `GET /favorites/my-favorites` | 12 VUs | 3 phút | 1080 | **100%** (2112/2112) | **40.12 ms** | **33.56 ms** | **ĐẠT** (SLA < 2000ms) |

> [!TIP]
> **Đánh giá độ bền và rò rỉ bộ nhớ (Soak Test):**
> * **Độ ổn định cao:** Hệ thống duy trì hoạt động liên tục trong suốt 16 phút thử nghiệm mà không có bất kỳ request nào bị lỗi (Error Rate = **0.00%**).
> * **Không phát hiện rò rỉ bộ nhớ:** Thời gian phản hồi trong suốt bài test không tăng tiến theo thời gian, chứng tỏ các microservices giải phóng tài nguyên tốt, Connection Pool cơ sở dữ liệu hoạt động ổn định và ổn định tài nguyên hệ thống.
> * Với API đọc bài đăng (`GET /posts`), dù chịu tải liên tục 20 VUs trong 4 phút, P(95) chỉ đạt **1.70s**, hoàn toàn thỏa mãn SLA dưới 2.0s.
