from app.db.session import get_cursor


def create_user(full_name: str, role: str | None = None, notes: str | None = None) -> int:
    with get_cursor() as cursor:
        cursor.execute(
            "INSERT INTO users (full_name, role, notes) VALUES (?, ?, ?)",
            (full_name, role, notes),
        )
        return cursor.lastrowid


def get_user(user_id: int) -> dict | None:
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()


def list_users(active_only: bool = True) -> list[dict]:
    with get_cursor() as cursor:
        if active_only:
            cursor.execute("SELECT * FROM users WHERE is_active = 1 ORDER BY full_name")
        else:
            cursor.execute("SELECT * FROM users ORDER BY full_name")
        return cursor.fetchall()


def set_user_active(user_id: int, is_active: bool) -> None:
    with get_cursor() as cursor:
        cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (is_active, user_id))
