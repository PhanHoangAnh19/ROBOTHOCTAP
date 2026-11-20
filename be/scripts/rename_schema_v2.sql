-- Tầng migration: chỉ đổi tên cấu trúc hiện có trong một transaction, giữ nguyên dữ liệu và identity.
-- Chạy một lần trên schema phiên bản trước; tên nguồn chỉ xuất hiện để thực hiện RENAME.
BEGIN;

ALTER TABLE events RENAME TO learning_events;
ALTER TABLE admin_users RENAME TO admin_accounts;
ALTER TABLE admin_sessions RENAME TO admin_login_sessions;
ALTER TABLE devices RENAME TO robots;
ALTER TABLE providers RENAME TO ai_service_configs;
ALTER TABLE settings RENAME TO app_settings;

ALTER TABLE learning_events RENAME COLUMN id TO event_id;
ALTER TABLE learning_events RENAME COLUMN timestamp TO occurred_at;
ALTER TABLE learning_events RENAME COLUMN event_type TO event_kind;
ALTER TABLE learning_events RENAME COLUMN category_name TO category_label;
ALTER TABLE learning_events RENAME COLUMN detail TO event_detail;

ALTER TABLE admin_accounts RENAME COLUMN id TO account_id;
ALTER TABLE admin_accounts RENAME COLUMN username TO login_name;
ALTER TABLE admin_accounts RENAME COLUMN password_hash TO hashed_password;

ALTER TABLE admin_login_sessions RENAME COLUMN id TO session_id;
ALTER TABLE admin_login_sessions RENAME COLUMN admin_id TO account_id;
ALTER TABLE admin_login_sessions RENAME COLUMN refresh_hash TO refresh_token_digest;
ALTER TABLE admin_login_sessions RENAME COLUMN revoked TO is_revoked;

ALTER TABLE robots RENAME COLUMN id TO robot_id;
ALTER TABLE robots RENAME COLUMN name TO robot_name;
ALTER TABLE robots RENAME COLUMN description TO robot_description;
ALTER TABLE robots RENAME COLUMN token_hash TO access_token_digest;

ALTER TABLE ai_service_configs RENAME COLUMN id TO service_id;
ALTER TABLE ai_service_configs RENAME COLUMN name TO service_name;
ALTER TABLE ai_service_configs RENAME COLUMN base_url TO endpoint_url;
ALTER TABLE ai_service_configs RENAME COLUMN model TO model_name;
ALTER TABLE ai_service_configs RENAME COLUMN api_key_encrypted TO encrypted_api_key;
ALTER TABLE ai_service_configs RENAME COLUMN config TO service_config;

ALTER TABLE prompts RENAME COLUMN id TO prompt_id;
ALTER TABLE prompts RENAME COLUMN mode TO learning_mode;
ALTER TABLE prompts RENAME COLUMN category_name TO category_label;
ALTER TABLE prompts RENAME COLUMN system_prompt TO instruction_text;

ALTER TABLE app_settings RENAME COLUMN id TO app_setting_id;
ALTER TABLE app_settings RENAME COLUMN key TO setting_key;
ALTER TABLE app_settings RENAME COLUMN value TO setting_value;

ALTER TABLE learning_events RENAME CONSTRAINT events_pkey TO learning_events_pkey;
ALTER TABLE admin_accounts RENAME CONSTRAINT admin_users_pkey TO admin_accounts_pkey;
ALTER TABLE admin_accounts RENAME CONSTRAINT admin_users_username_key TO idx_admin_accounts_login_name;
ALTER TABLE admin_login_sessions RENAME CONSTRAINT admin_sessions_pkey TO admin_login_sessions_pkey;
ALTER TABLE admin_login_sessions RENAME CONSTRAINT admin_sessions_admin_id_fkey TO fk_admin_login_sessions_admin_accounts;
ALTER TABLE robots RENAME CONSTRAINT devices_pkey TO robots_pkey;
ALTER TABLE robots RENAME CONSTRAINT devices_token_hash_key TO idx_robots_access_token_digest;
ALTER TABLE ai_service_configs RENAME CONSTRAINT providers_pkey TO ai_service_configs_pkey;
ALTER TABLE prompts RENAME CONSTRAINT prompts_mode_key TO idx_prompts_learning_mode;
ALTER TABLE app_settings RENAME CONSTRAINT settings_pkey TO app_settings_pkey;
ALTER TABLE app_settings RENAME CONSTRAINT settings_key_key TO idx_app_settings_setting_key;
ALTER INDEX providers_one_active RENAME TO idx_ai_service_configs_is_active;

ALTER SEQUENCE events_id_seq RENAME TO learning_events_event_id_seq;
ALTER SEQUENCE admin_users_id_seq RENAME TO admin_accounts_account_id_seq;
ALTER SEQUENCE admin_sessions_id_seq RENAME TO admin_login_sessions_session_id_seq;
ALTER SEQUENCE devices_id_seq RENAME TO robots_robot_id_seq;
ALTER SEQUENCE providers_id_seq RENAME TO ai_service_configs_service_id_seq;
ALTER SEQUENCE prompts_id_seq RENAME TO prompts_prompt_id_seq;
ALTER SEQUENCE settings_id_seq RENAME TO app_settings_app_setting_id_seq;

COMMIT;
