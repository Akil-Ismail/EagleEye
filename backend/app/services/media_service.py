import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings


def save_bytes(data: bytes, original_filename: str | None, subdir: str) -> str:
    settings = get_settings()
    target_dir = Path(settings.media_root) / subdir
    target_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(original_filename).suffix if original_filename else ""
    stored_name = f"{uuid.uuid4()}{suffix}"
    target_path = target_dir / stored_name

    with target_path.open("wb") as out_file:
        out_file.write(data)

    return str(target_path)


def save_upload(file: UploadFile, subdir: str) -> str:
    return save_bytes(file.file.read(), file.filename, subdir)
