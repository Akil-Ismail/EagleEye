import json

from app.db.session import get_cursor


def create_report(period_start, period_end, summary_text: str, log_ids_included: list[int]) -> int:
    if hasattr(period_start, "isoformat"):
        period_start = period_start.isoformat()
    if hasattr(period_end, "isoformat"):
        period_end = period_end.isoformat()

    with get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO reports (period_start, period_end, summary_text, log_ids_included)
            VALUES (?, ?, ?, ?)
            """,
            (period_start, period_end, summary_text, json.dumps(log_ids_included)),
        )
        return cursor.lastrowid


def list_reports(limit: int = 50, offset: int = 0) -> list[dict]:
    with get_cursor() as cursor:
        cursor.execute(
            "SELECT * FROM reports ORDER BY generated_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return cursor.fetchall()


def get_report(report_id: int) -> dict | None:
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
        return cursor.fetchone()
