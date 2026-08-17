from datetime import datetime, timezone

from fastapi import APIRouter, Form, HTTPException, UploadFile

from app.db.repository import users_repo
from app.schemas.users import UserResponse
from app.services import media_service
from app.services.face_service import extract_embedding
from app.vector.collections import upsert_face_embedding

router = APIRouter(prefix="/enroll", tags=["enroll"])


@router.post("", response_model=UserResponse)
def enroll_user(
    full_name: str = Form(...),
    role: str | None = Form(None),
    notes: str | None = Form(None),
    photos: list[UploadFile] = Form(...),
):
    photo_payloads = [(photo.filename, photo.file.read()) for photo in photos]

    embeddings = []
    for filename, data in photo_payloads:
        try:
            embeddings.append(extract_embedding(data))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=f"{filename}: {exc}") from exc

    user_id = users_repo.create_user(full_name=full_name, role=role, notes=notes)
    enrolled_at = datetime.now(timezone.utc).isoformat()

    for (filename, data), embedding in zip(photo_payloads, embeddings):
        media_service.save_bytes(data, filename, subdir=f"enrollment/{user_id}")
        upsert_face_embedding(user_id, embedding, media_upload_id=None, enrolled_at=enrolled_at)

    return users_repo.get_user(user_id)
