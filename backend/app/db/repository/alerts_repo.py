from app.db.session import get_cursor


def create_alert(log_id: int, alert_type: str) -> int:
    with get_cursor() as cursor:
        cursor.execute(
            "INSERT INTO alerts (log_id, type) VALUES (?, ?)",
            (log_id, alert_type),
        )
        return cursor.lastrowid


def list_alerts(resolved: bool | None = None, limit: int = 100, offset: int = 0) -> list[dict]:
    with get_cursor() as cursor:
        if resolved is None:
            cursor.execute(
                "SELECT * FROM alerts ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
        else:
            cursor.execute(
                "SELECT * FROM alerts WHERE resolved = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (resolved, limit, offset),
            )
        return cursor.fetchall()


def list_alerts_between(period_start: str, period_end: str, limit: int = 500) -> list[dict]:
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT * FROM alerts
            WHERE datetime(created_at) BETWEEN datetime(?) AND datetime(?)
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (period_start, period_end, limit),
        )
        return cursor.fetchall()


def resolve_alert(alert_id: int) -> None:
    with get_cursor() as cursor:
        cursor.execute(
            "UPDATE alerts SET resolved = 1, resolved_at = CURRENT_TIMESTAMP WHERE id = ?",
            (alert_id,),
        )
