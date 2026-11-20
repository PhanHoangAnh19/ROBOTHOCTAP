-- Tầng dữ liệu: khai báo bảng PostgreSQL; không có cột lưu ảnh hoặc video.
CREATE TABLE IF NOT EXISTS learning_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_kind TEXT NOT NULL,
    category_label TEXT NOT NULL,
    event_detail TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS admin_accounts (
    account_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    login_name TEXT NOT NULL CONSTRAINT idx_admin_accounts_login_name UNIQUE,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TABLE IF NOT EXISTS admin_login_sessions (
    session_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id BIGINT NOT NULL CONSTRAINT fk_admin_login_sessions_admin_accounts
        REFERENCES admin_accounts(account_id) ON DELETE CASCADE,
    refresh_token_digest TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE TABLE IF NOT EXISTS robots (
    robot_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    robot_name TEXT NOT NULL,
    robot_description TEXT NOT NULL DEFAULT '',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    access_token_digest TEXT CONSTRAINT idx_robots_access_token_digest UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS ai_service_configs (
    service_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_name TEXT NOT NULL,
    endpoint_url TEXT NOT NULL,
    model_name TEXT NOT NULL,
    encrypted_api_key TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    service_config JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_ai_service_configs_is_active
    ON ai_service_configs (is_active) WHERE is_active;
CREATE TABLE IF NOT EXISTS lesson_prompts (
    prompt_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    learning_mode TEXT NOT NULL CONSTRAINT idx_lesson_prompts_learning_mode UNIQUE,
    category_label TEXT NOT NULL,
    instruction_text TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS app_settings (
    app_setting_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    setting_key TEXT NOT NULL CONSTRAINT idx_app_settings_setting_key UNIQUE,
    setting_value JSONB NOT NULL
);
