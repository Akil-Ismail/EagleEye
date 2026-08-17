from app.db.session import get_cursor


def create_media_upload(
    source_type: str,
    file_path: str,
    original_filename: str | None = None,
) -> int:
    with get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO media_uploads (source_type, original_filename, file_path)
            VALUES (?, ?, ?)
            """,
            (source_type, original_filename, file_path),
        )
        return cursor.lastrowid


def get_media_upload(media_upload_id: int) -> dict | None:
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM media_uploads WHERE id = ?", (media_upload_id,))
        return cursor.fetchone()


def set_status(media_upload_id: int, status: str, processed_at_now: bool = False) -> None:
    with get_cursor() as cursor:
        if processed_at_now:
            cursor.execute(
                "UPDATE media_uploads SET status = ?, processed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, media_upload_id),
            )
        else:
            cursor.execute(
                "UPDATE media_uploads SET status = ? WHERE id = ?",
                (status, media_upload_id),
            )
