# be/ — Nhóm BE (Backend)

**Thành viên:** Phạm Trần Khánh Linh · Dương Thành Long · Trần Đặng Như Quỳnh
**Nhánh:** `be`

Backend Python 3.11+, FastAPI, PostgreSQL 16, psycopg 3; SQL thuần, không ORM.
Luồng xử lý: `api/routes → services → repositories → PostgreSQL`.
`backend_api.py` chỉ xuất lại `app`; bản gốc được giữ nguyên byte trong `backend_api.py.bak`.

## Chạy local (PowerShell)

```powershell
cd be
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env  # Chỉ chạy nếu chưa có .env
docker compose up -d
docker compose ps           # Đợi db ở trạng thái healthy
python -m uvicorn backend_api:app --port 8000
```

Cần Docker Desktop đang chạy ở chế độ Linux containers. `.env` chứa
`DATABASE_URL` và `POSTGRES_PASSWORD` tương ứng; giá trị mẫu chỉ nằm trong
`.env.example`. Biến môi trường có độ ưu tiên cao hơn `.env`.
Pool mở một lần trong lifespan; chạy `schema.sql` trong transaction rồi mới nhận request.
Thời gian đợi pool khi khởi động bằng `3 × DB_TIMEOUT` để libpq thử lần lượt
các địa chỉ IPv6/IPv4; thời gian lấy connection theo request là `DB_TIMEOUT`.
Kết nối hoặc DDL thất bại khiến khởi động thất bại. DDL có `IF NOT EXISTS`.
Volume `robothoctap_pgdata` giữ dữ liệu qua các lần khởi động.

`PORT` là cấu hình của ứng dụng; với lệnh uvicorn nêu trên, cổng do `--port` quyết định.
`TIMEZONE` mặc định `Asia/Bangkok` (UTC+7) để định dạng JSON thời gian như bản cũ;
PostgreSQL lưu `TIMESTAMPTZ`. Điều chỉnh nếu backend cũ chạy ở múi giờ khác.

Swagger: http://127.0.0.1:8000/docs. Health: http://127.0.0.1:8000/health.

## Hợp đồng API tương thích

Ba URL sau vẫn công khai như bản cũ để `ai/clients/` và dashboard tiếp tục sử dụng.
Không thêm lớp bọc JSON hoặc yêu cầu token vào chúng.

| Method | URL | Request | Response |
|---|---|---|---|
| POST | `/ask-ai` | `{"question":"...","mode":"GIAI_TOAN"}` | `{"answer":"..."}` |
| POST | `/sensor-event` | `{"event_type":"TU_THE_CO","detail":"..."}` | `{"status":"ok"}` |
| GET | `/events` | Không có | `{"summary":{...},"events":[...]}` |

`question`, `event_type`, `detail` là chuỗi; `mode` mặc định `GIAI_TOAN`,
giữ hỗ trợ chuỗi loại/chế độ lạ. `mode` lạ dùng prompt `THAC_MAC`,
loại cảm biến lạ có nhãn `Cảnh báo Hệ Thống`.
Mỗi câu hỏi ghi 5 phút, mỗi cảnh báo ghi 0 phút.

`GET /events` giữ tối đa 50 bản ghi theo `event_id DESC` trong DB;
trường JSON vẫn là `id`, thống kê chỉ tính trong cửa sổ đó:

```json
{
  "summary": {
    "total_study_minutes": 0,
    "posture_warnings": 0,
    "attention_warnings": 0,
    "ai_interactions": 0
  },
  "events": []
}
```

Mỗi sự kiện chỉ có `id`, `timestamp` (`YYYY-MM-DD HH:MM:SS`), `event_type`,
`category_name`, `detail`, `duration_minutes`. Không thêm cột nội bộ vào JSON.

## API quản trị và API có phiên bản

| Method | URL dưới `/api/v1` | Xác thực |
|---|---|---|
| GET | `/health` | Công khai |
| POST | `/auth/login` | JSON `username`, `password` |
| POST | `/auth/refresh` | JSON `refresh_token` |
| POST | `/auth/logout` | Bearer access JWT |
| GET, POST | `/devices`, `/providers`, `/prompts` | Bearer access JWT |
| GET, PUT, DELETE | `/devices/{id}`, `/providers/{id}`, `/prompts/{id}` | Bearer access JWT |
| POST, DELETE | `/devices/{id}/token` | Bearer access JWT |
| POST | `/providers/{id}/test` | Bearer access JWT |
| POST | `/sensor-event`, `/ask-ai` | Bearer token robot |
| GET | `/events`, `/stats` | Bearer access JWT |
| GET, PUT | `/settings` | Bearer access JWT |

Các API danh sách quản trị nhận `limit` (1–100, mặc định 50) và `offset` (≥0).
PUT thay toàn bộ dữ liệu nhập. Schema đầy đủ có trong `/docs`.
`/stats` trả bốn chỉ số của `summary`, không suy diễn số phiên học.

Tạo `JWT_SECRET` và `PROVIDER_ENCRYPTION_KEY` bằng các lệnh sau rồi điền vào `.env`:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
python scripts/seed_admin.py --username admin
```

Script nhập mật khẩu ẩn và không có mật khẩu mặc định. JWT_SECRET cần ít nhất
32 ký tự; khi chưa cấu hình, API auth trả 503, các API cũ vẫn sử dụng được.
Refresh token được xoay sau mỗi lần dùng; logout thu hồi cả phiên và access JWT.
Token robot chỉ trả rõ khi cấp, trong DB chỉ lưu SHA-256; cấp lại thay token cũ,
thu hồi hoặc vô hiệu hóa robot khiến token không sử dụng được.
Khóa provider được mã hóa Fernet trước khi INSERT/UPDATE; không trả khóa trong API.
Giữ nguyên khóa mã hóa nếu cần đọc các provider đã lưu.
Chỉ một provider được active tại một thời điểm; tắt provider cũ trước khi bật provider khác.

## API cấu hình (settings)

| Method | URL | Xác thực |
|---|---|---|
| GET | `/api/v1/settings` | Bearer access JWT |
| PUT | `/api/v1/settings` | Bearer access JWT |

GET trả toàn bộ cấu hình dạng `{key: value}`.
PUT nhận JSON object `{key: value}`, cập nhật bằng upsert, trả lại toàn bộ cấu hình.

Ba khóa mặc định (seed tự động khi khởi động):

| Khóa | Giá trị mặc định | Ý nghĩa |
|---|---|---|
| `posture_bad_threshold_seconds` | 10 | Ngưỡng phát hiện tư thế xấu (giây) |
| `reminder_cooldown_seconds` | 120 | Thời gian chờ giữa hai lần nhắc (giây) |
| `debounce_seconds` | 2 | Thời gian chống rung (giây) |

Giá trị phải là số nguyên dương. Khóa ngoài danh sách trả 422.

## LLM

Thứ tự chọn: provider active trong DB → `LLM_BASE_URL` trong `.env` → Gemini cũ.
Provider và `LLM_BASE_URL` sử dụng chuẩn OpenAI-compatible: URL cơ sở kết thúc
bằng `/v1` nếu dịch vụ yêu cầu; client nối `/chat/completions`.
Đặt `LLM_API_KEY`, `LLM_MODEL`, `LLM_TIMEOUT`, `LLM_RETRIES` trong `.env`.
Gemini tiếp tục dùng `GEMINI_API_KEY`, `GEMINI_MODEL`.
Khi không có khóa hoặc LLM lỗi, `/ask-ai` vẫn trả đúng câu offline cũ và ghi sự kiện.
Client chỉ gửi nội dung văn bản, retry có giới hạn cho lỗi mạng, 429 và 5xx;
log số token, độ trễ và loại lỗi, không log câu hỏi/đáp án/khóa.

## Riêng tư và kiểm thử

Tất cả schema sự kiện đặt `extra="forbid"`: các trường `image`, `base64`, `file`,
`video` hay trường lạ đều trả 422. Không có endpoint upload ảnh, không dùng
`UploadFile`, không có thao tác ghi media và không có cột lưu media.

Sau khi PostgreSQL healthy, chạy trong `be/`:

```powershell
python -m pytest tests -q -p no:cacheprovider
python -m compileall app
```

Từ thư mục gốc có thể chạy `be/.venv/Scripts/python -m compileall be/app`.
Test dùng PostgreSQL thật theo `.env`, override connection để rollback dữ liệu
sau từng test. Các kiểm thử provider dùng phản hồi LLM giả lập, không tiêu token thật.

## Phạm vi còn thiếu từ project gốc

- `dashboard.html` hiện thiếu hàm `triggerSensor` và phần cuối tài liệu HTML;
  không sửa vì nằm ngoài `be/`.
- Chưa có định nghĩa phiên học hay dữ liệu bắt đầu/kết thúc phiên trong API gốc;
  giữ cách tính thời lượng cũ, chưa thêm thống kê số phiên.
- Không có file dữ liệu SQLite trong `be/` lúc khảo sát; không có dữ liệu cũ để chuyển.
  Bản `.bak` chỉ để đối chiếu, không được import hay thực thi trong backend mới.

Chi tiết hiện trạng và kết quả chạy thật: [REFACTOR_REPORT.md](REFACTOR_REPORT.md).

## Tên dữ liệu PostgreSQL v2/v3

| Bảng | Cột trong database |
|---|---|
| `learning_events` | `event_id`, `occurred_at`, `event_kind`, `category_label`, `event_detail`, `duration_minutes` |
| `admin_accounts` | `account_id`, `login_name`, `hashed_password`, `is_active` |
| `admin_login_sessions` | `session_id`, `account_id`, `refresh_token_digest`, `expires_at`, `is_revoked` |
| `robots` | `robot_id`, `robot_name`, `robot_description`, `is_active`, `access_token_digest`, `created_at` |
| `ai_service_configs` | `service_id`, `service_name`, `endpoint_url`, `model_name`, `encrypted_api_key`, `is_active`, `service_config` |
| `lesson_prompts` | `prompt_id`, `learning_mode`, `category_label`, `instruction_text` |
| `app_settings` | `app_setting_id`, `setting_key`, `setting_value` |

Tên dữ liệu được tách khỏi DTO: repository dùng SQL alias để giữ mọi trường JSON
và đường dẫn API đã mô tả ở trên. Tham số CLI `--username` của script tạo admin
cũng giữ nguyên, lưu vào cột `login_name`. Không có thay đổi nghiệp vụ.

Với DB đã chạy trước bản v2, dừng backend rồi chạy các migration **một lần,
theo thứ tự v2 → v3** trước khi khởi động lại. Trong PowerShell, từ `be/`:

```powershell
Get-Content -Raw -Encoding UTF8 scripts/rename_schema_v2.sql | docker compose exec -T db psql -U robot -d robothoctap -v ON_ERROR_STOP=1
Get-Content -Raw -Encoding UTF8 scripts/rename_schema_v3.sql | docker compose exec -T db psql -U robot -d robothoctap -v ON_ERROR_STOP=1
python -m uvicorn backend_api:app --port 8000
```

DB đã ở v2 chỉ chạy `rename_schema_v3.sql` một lần. Migration v3 đổi tên bảng
prompt cùng PK, UNIQUE constraint/index và identity sequence; giữ nguyên cột,
dữ liệu, giá trị sequence và API `/api/v1/prompts`.
Mỗi migration chạy trong một transaction; chạy lại sẽ báo lỗi và rollback.
Cài mới chỉ cần `schema.sql` hiện tại, không chạy migration.
Không tạo bảng hoặc tính năng nghiệp vụ mới trong lần đổi tên này.
Báo cáo đối chiếu cấu trúc, dữ liệu và kiểm chứng:
[SCHEMA_V2_REPORT.md](SCHEMA_V2_REPORT.md). Báo cáo refactor trước được giữ nguyên.

Tham khảo: [psycopg pool](https://www.psycopg.org/psycopg3/docs/advanced/pool.html),
[pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).
