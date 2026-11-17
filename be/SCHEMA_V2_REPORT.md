<!-- Tầng tài liệu: đối chiếu đổi tên PostgreSQL v2, dữ liệu và hợp đồng API thực tế. -->
# Báo cáo đổi tên schema PostgreSQL — 17/11/2026

Đây là thay đổi tên thuần túy trong `be/`, không thay đổi kiểu dữ liệu hoặc nghiệp vụ.
Không thêm bảng, endpoint hay tính năng. Báo cáo lịch sử `REFACTOR_REPORT.md`
và bản gốc `backend_api.py.bak` giữ nguyên, được kiểm tra SHA-256 trước/sau.
Không commit, không push, không thay đổi file ngoài `be/`.

## Các điểm khác giả định và tên phát sinh theo Mục 3

Khảo sát PostgreSQL thật trước khi sửa: 7 bảng, 35 cột; hai sự kiện có ID 64, 65.
Tài khoản có tên đăng nhập, không có email hay vai trò; không tự thêm các cột đó.
Robot không có cột lần sử dụng cuối; provider không có cờ mặc định.
API key là một cột riêng đã mã hóa, không nằm trong JSONB; không đổi key JSONB.

| Cột thực tế phát sinh | Tên đã áp dụng | Lý do |
|---|---|---|
| `admin_users.username` | `admin_accounts.login_name` | Mô tả tên đăng nhập, giữ trường request `username` |
| `admin_sessions.refresh_hash` | `admin_login_sessions.refresh_token_digest` | Mô tả bản băm định danh refresh token |
| `devices.description` | `robots.robot_description` | Mô tả thiết bị robot |
| `settings.id` | `app_settings.app_setting_id` | Khóa chính theo tên bảng số ít |
| `prompts.id` | `prompts.prompt_id` | Khóa chính theo tên bảng số ít |
| `prompts.mode` | `prompts.learning_mode` | Chế độ học của prompt |
| `prompts.category_name` | `prompts.category_label` | Nhãn phân loại hiển thị |
| `prompts.system_prompt` | `prompts.instruction_text` | Nội dung chỉ dẫn văn bản |

Đây là danh sách 8 tên phát sinh để quản lý nhóm duyệt. Tên bảng `prompts`
giữ nguyên vì không có ánh xạ đổi tên bảng trong Mục 2; các cột áp dụng Mục 3.
`duration_minutes` và các cột được đặc tả yêu cầu giữ nguyên không thay đổi.

## Những quyết định triển khai cần ghi nhận

- Đổi tên cả 7 identity sequence cho đồng bộ với tên bảng/khóa mới, dùng
  `ALTER SEQUENCE ... RENAME`, không tạo lại, không reset và không đổi ownership.
- Đổi tên UNIQUE constraint sang tên `idx_<bảng>_<cột>` để backing index có đúng
  quy ước yêu cầu. PostgreSQL đổi tên index đi kèm khi rename constraint.
  Khóa chính và khóa ngoại dùng đúng quy ước trong đặc tả; `prompts_pkey` đã đúng
  nên giữ nguyên. Partial UNIQUE index giữ nguyên điều kiện `WHERE is_active`.
- Dữ liệu xác thực nội bộ sử dụng tên mới; các DTO JSON giữ nguyên qua SQL alias.
  Không thay đổi claim JWT, đường dẫn, tham số hoặc request/response.
- Migration chạy một lần trong một transaction `BEGIN`/`COMMIT`, không tự động
  chạy lại lúc startup. Cài mới dùng thẳng `schema.sql` với tên mới.
- Hai API POST được kiểm tra qua HTTP thật nên tạo dữ liệu thử có nhãn ngẫu nhiên.
  Sau kiểm chứng chỉ xóa các ID/nội dung thử do lượt kiểm tra này tạo; không xóa
  hay sửa hai sự kiện gốc. Cuối cùng số dòng và hash toàn bộ giá trị giữ nguyên.
  Identity sequence có thể tăng do test rollback/cleanup, không được tua lại.

## Kết quả sáu mục kiểm chứng

1. Migration chạy bằng `docker compose exec -T db psql ... -v ON_ERROR_STOP=1`,
   exit 0, kết thúc `COMMIT`. Cả 7 bảng có số dòng trước/sau bằng nhau;
   mọi giá trị được kiểm tra SHA-256 theo thứ tự khóa chính, không chỉ đếm dòng.
2. `information_schema` sau migration có đúng 7 bảng, 35 cột với tên mới.
   Không còn bảng hoặc cột thuộc danh sách phải đổi; không thêm cột giả định.
   Cài thử DDL trong namespace cô lập xác nhận cột, constraint, index và tên
   sequence trùng schema đã migration; namespace thử được rollback hoàn toàn.
3. Đã tìm kiếm nguồn và kiểm tra AST mọi `execute()` trong repository/scripts/tests.
   Cả 34 câu SQL chạy `EXPLAIN` thành công trên schema mới. Sau khi loại SQL alias,
   không còn định danh bảng/cột DB cũ trong những câu SQL đó. Tìm kiếm các tên nội bộ
   cũ trong code hoạt động không có kết quả.
4. `python -m pytest tests -q`: **19 passed, 1 warning in 11.42s**.
   Không bỏ test, không nới lỏng kỳ vọng JSON. Chỉ đổi SQL trong test theo tên mới;
   kiểm tra phản hồi provider được siết thành đúng tập 6 trường API hiện có.
   Cảnh báo duy nhất là deprecation Starlette TestClient/httpx từ thư viện.
5. `python -m uvicorn backend_api:app --port 8000` khởi động thành công.
   `/health`, `/events`, `/sensor-event`, `/ask-ai` đều HTTP 200; thêm `image`
   trả 422 với `extra_forbidden` và không tạo sự kiện. JSON `/events` và health
   trên dữ liệu gốc trùng hoàn toàn bản chụp trước migration; OpenAPI cũng trùng.
6. `python -m compileall be/app` từ gốc project thành công; `git diff --check`
   thành công. Git status chỉ có đường dẫn trong `be/`; không commit hoặc push.

Lưu ý về phép tìm kiếm chuỗi: không thể yêu cầu số lần xuất hiện tên cũ bằng 0
trong khi migration bắt buộc chứa tên nguồn và API bắt buộc giữ tên JSON/URL.
Những chỗ chủ ý còn tên cũ là nguồn lệnh `RENAME`, SQL alias/DTO/API, tên hàm hoặc
biến Python không phải cột DB, và các báo cáo đối chiếu lịch sử. Không có truy vấn
fallback sang bảng/cột cũ. Các bằng chứng lịch sử và `.bak` không được chỉnh sửa.

## Uvicorn chạy thật

Sau khi kiểm chứng đã dừng Uvicorn thử nghiệm để giải phóng cổng 8000.
PostgreSQL vẫn chạy; số dòng cuối cùng và ID gốc đã được kiểm tra lại qua psql.

```text
INFO:     Started server process [14952]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Các phần dưới được tạo từ bản chụp PostgreSQL và kết quả HTTP thực tế, không suy
ra từ DDL. Kiểu dữ liệu hiển thị đúng tên do `information_schema` trả về.

## Log migration thực tế

```text
BEGIN
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER INDEX
ALTER SEQUENCE
ALTER SEQUENCE
ALTER SEQUENCE
ALTER SEQUENCE
ALTER SEQUENCE
ALTER SEQUENCE
ALTER SEQUENCE
COMMIT
```

## information_schema: BEFORE / AFTER (35 columns)

| table_before | column_before | table_after | column_after | type_before | type_after |
| --- | --- | --- | --- | --- | --- |
| events | id | learning_events | event_id | bigint | bigint |
| events | timestamp | learning_events | occurred_at | timestamp with time zone | timestamp with time zone |
| events | event_type | learning_events | event_kind | text | text |
| events | category_name | learning_events | category_label | text | text |
| events | detail | learning_events | event_detail | text | text |
| events | duration_minutes | learning_events | duration_minutes | integer | integer |
| admin_users | id | admin_accounts | account_id | bigint | bigint |
| admin_users | username | admin_accounts | login_name | text | text |
| admin_users | password_hash | admin_accounts | hashed_password | text | text |
| admin_users | is_active | admin_accounts | is_active | boolean | boolean |
| admin_sessions | id | admin_login_sessions | session_id | bigint | bigint |
| admin_sessions | admin_id | admin_login_sessions | account_id | bigint | bigint |
| admin_sessions | refresh_hash | admin_login_sessions | refresh_token_digest | text | text |
| admin_sessions | expires_at | admin_login_sessions | expires_at | timestamp with time zone | timestamp with time zone |
| admin_sessions | revoked | admin_login_sessions | is_revoked | boolean | boolean |
| devices | id | robots | robot_id | bigint | bigint |
| devices | name | robots | robot_name | text | text |
| devices | description | robots | robot_description | text | text |
| devices | is_active | robots | is_active | boolean | boolean |
| devices | token_hash | robots | access_token_digest | text | text |
| devices | created_at | robots | created_at | timestamp with time zone | timestamp with time zone |
| providers | id | ai_service_configs | service_id | bigint | bigint |
| providers | name | ai_service_configs | service_name | text | text |
| providers | base_url | ai_service_configs | endpoint_url | text | text |
| providers | model | ai_service_configs | model_name | text | text |
| providers | api_key_encrypted | ai_service_configs | encrypted_api_key | text | text |
| providers | is_active | ai_service_configs | is_active | boolean | boolean |
| providers | config | ai_service_configs | service_config | jsonb | jsonb |
| prompts | id | prompts | prompt_id | bigint | bigint |
| prompts | mode | prompts | learning_mode | text | text |
| prompts | category_name | prompts | category_label | text | text |
| prompts | system_prompt | prompts | instruction_text | text | text |
| settings | id | app_settings | app_setting_id | bigint | bigint |
| settings | key | app_settings | setting_key | text | text |
| settings | value | app_settings | setting_value | jsonb | jsonb |

## Row counts: BEFORE / AFTER / FINAL

| table_before | table_after | rows_before | rows_after_migration | rows_final | all_values_sha256 |
| --- | --- | --- | --- | --- | --- |
| events | learning_events | 2 | 2 | 2 | MATCH |
| admin_users | admin_accounts | 0 | 0 | 0 | MATCH |
| admin_sessions | admin_login_sessions | 0 | 0 | 0 | MATCH |
| devices | robots | 0 | 0 | 0 | MATCH |
| providers | ai_service_configs | 0 | 0 | 0 | MATCH |
| prompts | prompts | 0 | 0 | 0 | MATCH |
| settings | app_settings | 0 | 0 | 0 | MATCH |

Original event IDs before / after / final: `64, 65`.

SHA-256 of all ordered event row values: `b226aa7056124b08be28a904fc2987c7827f6ba99c45521222f3289d56d6b5f7`.

## Constraints: BEFORE

| table_name | constraint_name | type | definition |
| --- | --- | --- | --- |
| admin_sessions | admin_sessions_admin_id_fkey | f | FOREIGN KEY (admin_id) REFERENCES admin_users(id) ON DELETE CASCADE |
| admin_sessions | admin_sessions_pkey | p | PRIMARY KEY (id) |
| admin_users | admin_users_pkey | p | PRIMARY KEY (id) |
| admin_users | admin_users_username_key | u | UNIQUE (username) |
| devices | devices_pkey | p | PRIMARY KEY (id) |
| devices | devices_token_hash_key | u | UNIQUE (token_hash) |
| events | events_pkey | p | PRIMARY KEY (id) |
| prompts | prompts_mode_key | u | UNIQUE (mode) |
| prompts | prompts_pkey | p | PRIMARY KEY (id) |
| providers | providers_pkey | p | PRIMARY KEY (id) |
| settings | settings_key_key | u | UNIQUE (key) |
| settings | settings_pkey | p | PRIMARY KEY (id) |

## Indexes: BEFORE

| table_name | index_name | definition |
| --- | --- | --- |
| admin_sessions | admin_sessions_pkey | CREATE UNIQUE INDEX admin_sessions_pkey ON public.admin_sessions USING btree (id) |
| admin_users | admin_users_pkey | CREATE UNIQUE INDEX admin_users_pkey ON public.admin_users USING btree (id) |
| admin_users | admin_users_username_key | CREATE UNIQUE INDEX admin_users_username_key ON public.admin_users USING btree (username) |
| devices | devices_pkey | CREATE UNIQUE INDEX devices_pkey ON public.devices USING btree (id) |
| devices | devices_token_hash_key | CREATE UNIQUE INDEX devices_token_hash_key ON public.devices USING btree (token_hash) |
| events | events_pkey | CREATE UNIQUE INDEX events_pkey ON public.events USING btree (id) |
| prompts | prompts_mode_key | CREATE UNIQUE INDEX prompts_mode_key ON public.prompts USING btree (mode) |
| prompts | prompts_pkey | CREATE UNIQUE INDEX prompts_pkey ON public.prompts USING btree (id) |
| providers | providers_one_active | CREATE UNIQUE INDEX providers_one_active ON public.providers USING btree (is_active) WHERE is_active |
| providers | providers_pkey | CREATE UNIQUE INDEX providers_pkey ON public.providers USING btree (id) |
| settings | settings_key_key | CREATE UNIQUE INDEX settings_key_key ON public.settings USING btree (key) |
| settings | settings_pkey | CREATE UNIQUE INDEX settings_pkey ON public.settings USING btree (id) |

## Identity sequences: BEFORE

| sequence_name | last_value_at_snapshot |
| --- | --- |
| admin_sessions_id_seq | 6 |
| admin_users_id_seq | 6 |
| devices_id_seq | 3 |
| events_id_seq | 191 |
| prompts_id_seq | 3 |
| providers_id_seq | 3 |
| settings_id_seq | None |

## Constraints: AFTER

| table_name | constraint_name | type | definition |
| --- | --- | --- | --- |
| admin_accounts | admin_accounts_pkey | p | PRIMARY KEY (account_id) |
| admin_accounts | idx_admin_accounts_login_name | u | UNIQUE (login_name) |
| admin_login_sessions | admin_login_sessions_pkey | p | PRIMARY KEY (session_id) |
| admin_login_sessions | fk_admin_login_sessions_admin_accounts | f | FOREIGN KEY (account_id) REFERENCES admin_accounts(account_id) ON DELETE CASCADE |
| ai_service_configs | ai_service_configs_pkey | p | PRIMARY KEY (service_id) |
| app_settings | app_settings_pkey | p | PRIMARY KEY (app_setting_id) |
| app_settings | idx_app_settings_setting_key | u | UNIQUE (setting_key) |
| learning_events | learning_events_pkey | p | PRIMARY KEY (event_id) |
| prompts | idx_prompts_learning_mode | u | UNIQUE (learning_mode) |
| prompts | prompts_pkey | p | PRIMARY KEY (prompt_id) |
| robots | idx_robots_access_token_digest | u | UNIQUE (access_token_digest) |
| robots | robots_pkey | p | PRIMARY KEY (robot_id) |

## Indexes: AFTER

| table_name | index_name | definition |
| --- | --- | --- |
| admin_accounts | admin_accounts_pkey | CREATE UNIQUE INDEX admin_accounts_pkey ON public.admin_accounts USING btree (account_id) |
| admin_accounts | idx_admin_accounts_login_name | CREATE UNIQUE INDEX idx_admin_accounts_login_name ON public.admin_accounts USING btree (login_name) |
| admin_login_sessions | admin_login_sessions_pkey | CREATE UNIQUE INDEX admin_login_sessions_pkey ON public.admin_login_sessions USING btree (session_id) |
| ai_service_configs | ai_service_configs_pkey | CREATE UNIQUE INDEX ai_service_configs_pkey ON public.ai_service_configs USING btree (service_id) |
| ai_service_configs | idx_ai_service_configs_is_active | CREATE UNIQUE INDEX idx_ai_service_configs_is_active ON public.ai_service_configs USING btree (is_active) WHERE is_active |
| app_settings | app_settings_pkey | CREATE UNIQUE INDEX app_settings_pkey ON public.app_settings USING btree (app_setting_id) |
| app_settings | idx_app_settings_setting_key | CREATE UNIQUE INDEX idx_app_settings_setting_key ON public.app_settings USING btree (setting_key) |
| learning_events | learning_events_pkey | CREATE UNIQUE INDEX learning_events_pkey ON public.learning_events USING btree (event_id) |
| prompts | idx_prompts_learning_mode | CREATE UNIQUE INDEX idx_prompts_learning_mode ON public.prompts USING btree (learning_mode) |
| prompts | prompts_pkey | CREATE UNIQUE INDEX prompts_pkey ON public.prompts USING btree (prompt_id) |
| robots | idx_robots_access_token_digest | CREATE UNIQUE INDEX idx_robots_access_token_digest ON public.robots USING btree (access_token_digest) |
| robots | robots_pkey | CREATE UNIQUE INDEX robots_pkey ON public.robots USING btree (robot_id) |

## Identity sequences: AFTER

| sequence_name | last_value_at_snapshot |
| --- | --- |
| admin_accounts_account_id_seq | 8 |
| admin_login_sessions_session_id_seq | 8 |
| ai_service_configs_service_id_seq | 4 |
| app_settings_app_setting_id_seq | None |
| learning_events_event_id_seq | 254 |
| prompts_prompt_id_seq | 4 |
| robots_robot_id_seq | 4 |

## Verification metadata

```json
{
  "sql_statements_verified": 34,
  "fresh_schema_verified": true,
  "openapi_identical": true,
  "json_before_after_identical": true,
  "cleaned_up_live_test_ids": [
    257,
    258
  ],
  "cleaned_up_prior_test_ids": [
    256
  ],
  "history_sha256_unchanged": "b041ed044c9c8fb2da618402235b3fbb52d422c2603b3dbadd0d970e2b1bfb51",
  "backup_sha256_unchanged": "098dddd1eb940b3f764fecbc9108b52ffa9234dc11d17198f21d4e829e44eb0c"
}
```

## HTTP: actual requests and responses

### 1. GET /health - HTTP 200

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

### 2. GET /events - HTTP 200

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

### 3. POST /sensor-event - HTTP 200

```json
{
  "method": "POST",
  "path": "/sensor-event",
  "request": {
    "event_type": "TU_THE_CO",
    "detail": "PostgreSQL rename verification SCHEMA_V2_62bf63610247"
  },
  "status": 200,
  "response": {
    "status": "ok"
  }
}
```

### 4. POST /ask-ai - HTTP 200

```json
{
  "method": "POST",
  "path": "/ask-ai",
  "request": {
    "question": "1 + 1 = ? [SCHEMA_V2_62bf63610247]",
    "mode": "GIAI_TOAN"
  },
  "status": 200,
  "response": {
    "answer": "[Chế độ Offline] Đã nhận câu hỏi '1 + 1 = ? [SCHEMA_V2_62bf63610247]'. (Kiểm tra lại API Key để AI trả lời thực tế)."
  }
}
```

### 5. GET /events - HTTP 200

```json
{
  "method": "GET",
  "path": "/events",
  "request": null,
  "status": 200,
  "response": {
    "summary": {
      "total_study_minutes": 10,
      "posture_warnings": 2,
      "attention_warnings": 0,
      "ai_interactions": 2
    },
    "events": [
      {
        "id": 258,
        "timestamp": "2026-11-17 02:12:53",
        "event_type": "GIAI_TOAN",
        "category_name": "Giải Toán",
        "detail": "Hỏi: 1 + 1 = ? [SCHEMA_V2_62bf63610247] ➔ Đáp: [Chế độ Offline] Đã nhận câu hỏi '1 + 1 = ? [SCHEMA_V2_62bf63610247]'. (Kiểm tra lại API Key để AI trả lời thực tế).",
        "duration_minutes": 5
      },
      {
        "id": 257,
        "timestamp": "2026-11-17 02:12:53",
        "event_type": "TU_THE_CO",
        "category_name": "Cảnh báo Gập Cổ",
        "detail": "PostgreSQL rename verification SCHEMA_V2_62bf63610247",
        "duration_minutes": 0
      },
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

### 6. POST /sensor-event - HTTP 422

```json
{
  "method": "POST",
  "path": "/sensor-event",
  "request": {
    "event_type": "TU_THE_CO",
    "detail": "SCHEMA_V2_62bf63610247",
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

### 7. GET /events - HTTP 200

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
