<!-- Tầng tài liệu: báo cáo hiện trạng, thay đổi kiến trúc và bằng chứng kiểm chứng thực tế. -->
# Báo cáo tổ chức lại backend — 17/11/2026

Chỉ thay đổi bên trong `be/`. Không commit, không push. Các file `ai/`,
`web-service/`, README gốc và `.gitignore` giữ nguyên.

## Cây thư mục

Không liệt kê `.venv/`, `__pycache__/` và file tạm của kiểm chứng.
`.env` được sinh local với bí mật ngẫu nhiên, được `.gitignore` hiện có bỏ qua.

```text
be/
├── backend_api.py
├── backend_api.py.bak
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── dependencies.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py
│   │       ├── auth.py
│   │       ├── devices.py
│   │       ├── providers.py
│   │       ├── prompts.py
│   │       ├── events.py
│   │       └── stats.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── devices.py
│   │   ├── providers.py
│   │   ├── prompts.py
│   │   ├── events.py
│   │   └── stats.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── device_service.py
│   │   ├── provider_service.py
│   │   ├── prompt_service.py
│   │   ├── event_service.py
│   │   └── stats_service.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── admin_user_repository.py
│   │   ├── device_repository.py
│   │   ├── provider_repository.py
│   │   ├── prompt_repository.py
│   │   ├── event_repository.py
│   │   └── setting_repository.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── pool.py
│   │   └── schema.sql
│   ├── platform/
│   │   ├── __init__.py
│   │   ├── ai_client.py
│   │   └── crypto.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── admin_auth.py
│   │   ├── device_auth.py
│   │   ├── cors.py
│   │   ├── logging.py
│   │   └── error_handler.py
│   └── common/
│       ├── __init__.py
│       ├── response.py
│       ├── exceptions.py
│       ├── pagination.py
│       ├── logger.py
│       └── timeutil.py
├── scripts/
│   └── seed_admin.py
├── tests/
│   ├── conftest.py
│   └── test_health.py
├── docker-compose.yml
├── .env.example
├── .env                     (local, không theo dõi git)
├── requirements.txt
├── README.md
└── REFACTOR_REPORT.md
```

## Hiện trạng đã in trước khi sửa

Đã đọc toàn bộ `backend_api.py`, requirements, README của BE,
`dashboard.html`, `main_monitor.py`, `ai/clients/backend_client.py` và
`ai/clients/__init__.py` trước khi thay đổi file.

| Method | URL | Request cũ | Response cũ |
|---|---|---|---|
| POST | `/ask-ai` | `question: str`, `mode: str = GIAI_TOAN` | `{"answer":str}` |
| POST | `/sensor-event` | `event_type: str`, `detail: str` | `{"status":"ok"}` |
| GET | `/events` | Không có | `{"summary":{total_study_minutes,posture_warnings,attention_warnings,ai_interactions},"events":[...]}` |

Schema mỗi bản ghi: `id: int`, `timestamp: str` dạng `YYYY-MM-DD HH:MM:SS`,
`event_type: str`, `category_name: str`, `detail: str`, `duration_minutes: int`.

| Nơi dùng SQLite cũ | Câu SQL / thao tác |
|---|---|
| `init_db()` | `sqlite3.connect("robot_events.db")`; DDL bên dưới |
| `log_event()` | `sqlite3.connect(...)`; `INSERT INTO events (timestamp, event_type, category_name, detail, duration_minutes) VALUES (?, ?, ?, ?, ?)`; commit |
| `get_events()` | `sqlite3.connect(...)`; `sqlite3.Row`; `SELECT * FROM events ORDER BY id DESC LIMIT 50` |
| UPDATE / DELETE | Không có |

```sql
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    event_type TEXT,
    category_name TEXT,
    detail TEXT,
    duration_minutes INTEGER DEFAULT 0
);
```

| Nơi gọi | Endpoint và payload thực tế |
|---|---|
| Dashboard `fetchEvents` | GET `/events`, đọc trực tiếp `summary` và `events` |
| Dashboard `sendQuestion` | POST `/ask-ai`, `{question:q,mode:mode}` |
| Dashboard các nút cảm biến | Tham chiếu `triggerSensor(type,detail)` nhưng thiếu định nghĩa; không có lệnh gọi HTTP tương ứng trong file hiện tại |
| AI `send_posture_alert` | POST `/sensor-event`, `{event_type:TU_THE_CO hoặc TU_THE_VAI,detail:"[MediaPipe AI] ..."}` |
| AI `send_attention_alert` | POST `/sensor-event`, `{event_type:MAT_TAP_TRUNG,detail:"[MediaPipe AI] ..."}` |
| `main_monitor.py` | Gọi `BackendEventPublisher.send_posture_alert`; ảnh chỉ được xử lý tại AI |

## Đối chiếu endpoint trước và sau

| Method | URL trước | URL sau | JSON vào trước → sau | JSON ra trước → sau |
|---|---|---|---|---|
| POST | `/ask-ai` | `/ask-ai` | `{question,mode?}` → giữ nguyên | `{answer}` → giữ nguyên |
| POST | `/sensor-event` | `/sensor-event` | `{event_type,detail}` → giữ nguyên | `{status:"ok"}` → giữ nguyên |
| GET | `/events` | `/events` | Không có → giữ nguyên | `{summary:{4 chỉ số},events:[6 trường]}` → giữ nguyên |

Thay đổi validation bắt buộc theo đặc tả riêng tư: trường ngoài schema bị trả 422,
thay vì bị bỏ qua như Pydantic mặc định của bản cũ. Không thêm lớp bọc JSON.
Ba URL cũ không yêu cầu token, giữ nguyên CORS.

Thứ tự ID giảm dần, giới hạn 50 và thống kê trong 50 bản ghi được giữ nguyên.
Mỗi câu hỏi vẫn ghi 5 phút, mỗi cảnh báo 0 phút. Chế độ lạ giữ nguyên giá trị
`event_type`, dùng prompt và nhãn `THAC_MAC`; cảnh báo lạ giữ nhãn hệ thống.
Gemini và câu trả lời offline giữ nguyên, đồng thời thêm client OpenAI-compatible.

Các route mới theo yêu cầu gồm `/health` và các module dưới `/api/v1`:
auth login/logout/refresh; CRUD devices/providers/prompts; cấp/thu hồi token robot;
test provider; alias hỏi đáp/cảnh báo có token robot; lịch sử và thống kê có JWT admin.
Danh sách phương thức và payload đầy đủ nằm trong README và `/docs`.
Không có API phiên học vì bản cũ chưa định nghĩa dữ liệu hoặc quy tắc tính phiên.

## Kiến trúc và dữ liệu

- Route chỉ nhận schema, gọi service, trả qua `common/response.py`.
- Service không import FastAPI; repository chứa SQL psycopg với `%s` và tham số riêng.
- Pool mở một lần mỗi lifespan và đóng khi shutdown; DDL chạy trong transaction.
  Trên máy Windows này, IPv6 `::1` timeout trước khi libpq kết nối IPv4;
  thời gian chờ khởi tạo pool cho phép thử lần lượt các địa chỉ của `localhost`.
- Dùng `BIGINT GENERATED ALWAYS AS IDENTITY`, `RETURNING id`, `TIMESTAMPTZ`,
  `BOOLEAN` và `JSONB`. Sự kiện chỉ lưu các cột văn bản/số/thời gian cũ.
- `clock_timestamp()` ghi thời điểm INSERT sau khi LLM trả lời như bản cũ;
  JSON thời gian vẫn định dạng UTC+7, không xuất kiểu ISO mới cho dashboard.
- Connection dependency commit/rollback trước khi gửi phản hồi thành công.
- JWT có phiên được thu hồi khi logout, refresh xoay một lần; robot lưu hash token;
  API key provider lưu Fernet ciphertext, không trả trong JSON quản trị.
- Không có schema ảnh/video, upload, ghi media hoặc ghi request body vào log.
  Các schema sự kiện, kể cả schema kết quả và thống kê, kế thừa `extra="forbid"`.

## Kết quả chạy thật

Môi trường: Windows, Python 3.13.11 (thỏa Python 3.11+), PostgreSQL 16.16 từ
image `postgres:16`, psycopg 3.3.9, psycopg-pool 3.3.3.

`docker compose up -d` chạy trong `be/`, exit 0:

```text
Network be_default Created
Volume be_robothoctap_pgdata Created
Container be-db-1 Created
Container be-db-1 Started
```

`docker compose ps` và `docker compose exec -T db pg_isready -U robot -d robothoctap`:

```text
NAME      IMAGE         SERVICE   STATUS                   PORTS
be-db-1   postgres:16   db        Up 2 minutes (healthy)   127.0.0.1:5432->5432/tcp
/var/run/postgresql:5432 - accepting connections
```

Đã chạy nguyên lệnh `python -m uvicorn backend_api:app --port 8000` bằng Python của
virtualenv trong `be/`:

```text
INFO:     Started server process [22964]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

`python -m pytest tests -q -p no:cacheprovider` đã đạt 19 test trên PostgreSQL thật.
Kết quả cuối: `19 passed, 1 warning in 11.59s`.
Một cảnh báo deprecation của Starlette về TestClient/httpx; không có test lỗi.
Test rollback từng transaction, không để lại dữ liệu quản trị/robot/provider/prompt.
Kiểm thử bao gồm health, hai API cũ, cửa sổ 50 sự kiện, loại/chế độ lạ,
từ chối image/base64/file/video/trường lạ, dữ liệu không phải văn bản/multipart,
JWT refresh/logout, robot token, CRUD provider/prompt và JSON LLM sai cấu trúc.
Các test provider dùng phản hồi LLM giả lập; HTTP live `/ask-ai` dùng nhánh offline
do không cấu hình khóa LLM thật. Không tuyên bố đã gọi thành công provider thật.

`python -m compileall be/app` từ gốc project: exit 0.
`git diff --check`: exit 0. Không có thay đổi ngoài `be/`.
Git blob hash của `.bak` và `HEAD:be/backend_api.py` trùng nhau:

```text
6db8db6398fea32d24696f25a480d66f98711759
```

Đối chiếu AST bản gốc với OpenAPI ứng dụng mới xác nhận cả 3 cặp method/URL
đều tồn tại. JSON Schema của AskPayload và SensorEventPayload đều có
`additionalProperties: false`, không có trường ảnh/file/base64/video.
`pip check`: `No broken requirements found.`

Đối chiếu `information_schema.columns` trong PostgreSQL thật:

| Bảng/cột | Kiểu thực tế |
|---|---|
| `events.id` | `bigint` |
| `events.timestamp` | `timestamp with time zone` |
| `events.event_type`, `category_name`, `detail` | `text` |
| `events.duration_minutes` | `integer` |
| `admin_sessions.revoked`, `admin_users.is_active`, `devices.is_active`, `providers.is_active` | `boolean` |
| `providers.config`, `settings.value` | `jsonb` |

Sau kiểm chứng đã dừng Uvicorn thử nghiệm để giải phóng cổng 8000.
Container PostgreSQL tiếp tục chạy, lần kiểm tra cuối vẫn `healthy`.
DB giữ hai sự kiện thử HTTP văn bản (id 64, 65); payload bị từ chối không tạo sự kiện.
Các khoảng trống ID là do PostgreSQL identity không rollback sequence trong test.

## TODO và điểm chưa có đặc tả

1. Dashboard thiếu `triggerSensor` và phần kết thúc HTML: cần nhóm dashboard sửa
   trong công việc riêng; lần này không thay đổi file ngoài `be/`.
2. Chưa có khái niệm bắt đầu/kết thúc phiên học, mã phiên hoặc quy tắc tính phiên:
   chưa thêm trường đếm phiên; tiếp tục dùng thống kê cũ.
3. Không có file SQLite trong `be/` lúc khảo sát để chuyển dữ liệu lịch sử.
   Nếu có dữ liệu ở máy triển khai khác, cần thống nhất quy trình nhập riêng.
4. Chưa kiểm thử dịch vụ LLM thật vì không có khóa thật; cần cấu hình `.env` hoặc
   provider mã hóa, rồi gọi API test kết nối khi triển khai.

Không có format endpoint cũ nào phải đoán. Các quyết định cho API mới được mô tả
trong README và OpenAPI; không thay đổi hợp đồng của hai client đang sử dụng.

## HTTP request/response thực tế

Các kết quả dưới đây được thu trực tiếp từ Uvicorn tại `127.0.0.1:8000`,
không qua TestClient. Payload từ chối chỉ dùng chuỗi thử nghiệm, không dùng ảnh thật.

### 1. GET /health ? HTTP 200

```json
{
  "method": "GET",
  "path": "/health",
  "request": null,
  "status": 200,
  "response": {
    "status": "ok",
    "database": "ok"
  }
}
```

### 2. GET /events ? HTTP 200

```json
{
  "method": "GET",
  "path": "/events",
  "request": null,
  "status": 200,
  "response": {
    "summary": {
      "total_study_minutes": 0,
      "posture_warnings": 0,
      "attention_warnings": 0,
      "ai_interactions": 0
    },
    "events": []
  }
}
```

### 3. POST /sensor-event ? HTTP 200

```json
{
  "method": "POST",
  "path": "/sensor-event",
  "request": {
    "event_type": "TU_THE_CO",
    "detail": "Kiem thu PostgreSQL"
  },
  "status": 200,
  "response": {
    "status": "ok"
  }
}
```

### 4. POST /ask-ai ? HTTP 200

```json
{
  "method": "POST",
  "path": "/ask-ai",
  "request": {
    "question": "1 + 1 = ?",
    "mode": "GIAI_TOAN"
  },
  "status": 200,
  "response": {
    "answer": "[Chế độ Offline] Đã nhận câu hỏi '1 + 1 = ?'. (Kiểm tra lại API Key để AI trả lời thực tế)."
  }
}
```

### 5. GET /events ? HTTP 200

```json
{
  "method": "GET",
  "path": "/events",
  "request": null,
  "status": 200,
  "response": {
    "summary": {
      "total_study_minutes": 5,
      "posture_warnings": 1,
      "attention_warnings": 0,
      "ai_interactions": 1
    },
    "events": [
      {
        "id": 65,
        "timestamp": "2026-11-17 01:23:08",
        "event_type": "GIAI_TOAN",
        "category_name": "Giải Toán",
        "detail": "Hỏi: 1 + 1 = ? ➔ Đáp: [Chế độ Offline] Đã nhận câu hỏi '1 + 1 = ?'. (Kiểm tra lại API Key để AI trả lời thực tế).",
        "duration_minutes": 5
      },
      {
        "id": 64,
        "timestamp": "2026-11-17 01:23:08",
        "event_type": "TU_THE_CO",
        "category_name": "Cảnh báo Gập Cổ",
        "detail": "Kiem thu PostgreSQL",
        "duration_minutes": 0
      }
    ]
  }
}
```

### 6. POST /sensor-event ? HTTP 422

```json
{
  "method": "POST",
  "path": "/sensor-event",
  "request": {
    "event_type": "TU_THE_CO",
    "detail": "Kiem thu quyen rieng tu",
    "image": "rejected"
  },
  "status": 422,
  "response": {
    "detail": [
      {
        "type": "extra_forbidden",
        "loc": [
          "body",
          "image"
        ],
        "msg": "Extra inputs are not permitted",
        "input": "rejected"
      }
    ]
  }
}
```
