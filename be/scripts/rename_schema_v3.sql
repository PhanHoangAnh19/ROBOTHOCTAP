-- Tầng migration: chỉ đổi tên bảng prompt, constraint/index và identity sequence trong một transaction.
-- Chạy một lần sau v2; không thay đổi cột, dữ liệu hoặc giá trị sequence.
BEGIN;

ALTER TABLE prompts RENAME TO lesson_prompts;
ALTER TABLE lesson_prompts RENAME CONSTRAINT prompts_pkey TO lesson_prompts_pkey;
ALTER INDEX idx_prompts_learning_mode RENAME TO idx_lesson_prompts_learning_mode;
ALTER SEQUENCE prompts_prompt_id_seq RENAME TO lesson_prompts_prompt_id_seq;

COMMIT;
