from app.db.session import get_cursor


def create_access_log(
    confidence_score: float,
    decision: str,
    user_id: int | None = None,
    media_upload_id: int | None = None,
    camera_id: str | None = None,
    frame_timestamp_ms: int | None = None,
    liveness_passed: bool | None = None,
    snapshot_path: str | None = None,
) -> int:
    with get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO access_logs (
                user_id, media_upload_id, camera_id, frame_timestamp_ms,
                confidence_score, liveness_passed, decision, snapshot_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                media_upload_id,
                camera_id,
                frame_timestamp_ms,
                confidence_score,
                liveness_passed,
                decision,
                snapshot_path,
            ),
        )
        return cursor.lastrowid


def get_log(log_id: int) -> dict | None:
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM access_logs WHERE id = ?", (log_id,))
        return cursor.fetchone()


def list_logs(limit: int = 100, offset: int = 0, decision: str | None = None) -> list[dict]:
    with get_cursor() as cursor:
        if decision:
            cursor.execute(
                "SELECT * FROM access_logs WHERE decision = ? "
                "ORDER BY event_timestamp DESC LIMIT ? OFFSET ?",
                (decision, limit, offset),
            )
        else:
            cursor.execute(
                "SELECT * FROM access_logs ORDER BY event_timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
        return cursor.fetchall()


def list_logs_between(period_start: str, period_end: str, limit: int = 500) -> list[dict]:
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT * FROM access_logs
            WHERE datetime(event_timestamp) BETWEEN datetime(?) AND datetime(?)
            ORDER BY event_timestamp DESC
            LIMIT ?
            """,
            (period_start, period_end, limit),
        )
        return cursor.fetchall()


def list_logs_by_media_upload(media_upload_id: int) -> list[dict]:
    with get_cursor() as cursor:
        cursor.execute(
            "SELECT * FROM access_logs WHERE media_upload_id = ? ORDER BY frame_timestamp_ms",
            (media_upload_id,),
        )
        return cursor.fetchall()


def count_recent_unknown(user_id_is_null: bool, within_minutes: int) -> int:
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*) AS total FROM access_logs
            WHERE decision = 'unknown'
              AND event_timestamp >= datetime('now', '-' || ? || ' minutes')
            """,
            (within_minutes,),
        )
        row = cursor.fetchone()
        return row["total"] if row else 0
