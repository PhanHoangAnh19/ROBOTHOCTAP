# Tầng repository: CRUD prompt và lấy cấu hình giảng giải theo chế độ.
def list_all(connection, limit, offset):
    return connection.execute(
        "SELECT prompt_id AS id, learning_mode AS mode, category_label AS category_name, "
        "instruction_text AS system_prompt FROM lesson_prompts ORDER BY prompt_id LIMIT %s OFFSET %s", (limit, offset),
    ).fetchall()


def get(connection, prompt_id):
    return connection.execute(
        "SELECT prompt_id AS id, learning_mode AS mode, category_label AS category_name, "
        "instruction_text AS system_prompt FROM lesson_prompts WHERE prompt_id = %s", (prompt_id,),
    ).fetchone()


def by_mode(connection, mode):
    return connection.execute(
        "SELECT prompt_id AS id, learning_mode AS mode, category_label AS category_name, "
        "instruction_text AS system_prompt FROM lesson_prompts WHERE learning_mode = %s", (mode,),
    ).fetchone()


def insert(connection, mode, category_name, system_prompt):
    return connection.execute(
        "INSERT INTO lesson_prompts (learning_mode, category_label, instruction_text) VALUES (%s, %s, %s) RETURNING prompt_id",
        (mode, category_name, system_prompt),
    ).fetchone()["prompt_id"]


def update(connection, prompt_id, mode, category_name, system_prompt):
    connection.execute(
        "UPDATE lesson_prompts SET learning_mode = %s, category_label = %s, instruction_text = %s WHERE prompt_id = %s",
        (mode, category_name, system_prompt, prompt_id),
    )


def delete(connection, prompt_id):
    connection.execute("DELETE FROM lesson_prompts WHERE prompt_id = %s", (prompt_id,))
