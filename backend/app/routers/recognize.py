from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile

from app.db.repository import logs_repo, media_repo, users_repo
from app.schemas.recognition import RecognitionResult, VideoJobResponse, VideoJobStatusResponse
from app.services import media_service
from app.services.face_service import detect_faces
from app.services.recognition_service import match_embedding, record_recognition_event
from app.workers.video_processing import process_video_job

router = APIRouter(prefix="/recognize", tags=["recognize"])


@router.post("/frame", response_model=list[RecognitionResult])
def recognize_frame(image: UploadFile, camera_id: str | None = None):
    image_bytes = image.file.read()
    try:
        faces = detect_faces(image_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    snapshot_path = media_service.save_bytes(image_bytes, image.filename, subdir="snapshots")

    results = []
    for face in faces:
        user_id, confidence_score = match_embedding(face["embedding"])
        log_id, decision = record_recognition_event(
            user_id=user_id,
            confidence_score=confidence_score,
            liveness_passed=face["is_live"],
            camera_id=camera_id,
            snapshot_path=snapshot_path,
        )
        user = users_repo.get_user(user_id) if user_id else None
        results.append(
            RecognitionResult(
                decision=decision,
                user_id=user_id,
                full_name=user["full_name"] if user else None,
                confidence_score=confidence_score,
                liveness_passed=face["is_live"],
                log_id=log_id,
            )
        )
    return results


@router.post("/video", response_model=VideoJobResponse)
def recognize_video(video: UploadFile, background_tasks: BackgroundTasks):
    stored_path = media_service.save_upload(video, subdir="uploads/video")
    media_upload_id = media_repo.create_media_upload(
        source_type="upload_video",
        file_path=stored_path,
        original_filename=video.filename,
    )

    background_tasks.add_task(process_video_job, media_upload_id)

    return VideoJobResponse(media_upload_id=media_upload_id, status="pending")


@router.get("/video/{media_upload_id}", response_model=VideoJobStatusResponse)
def get_video_job_status(media_upload_id: int):
    upload = media_repo.get_media_upload(media_upload_id)
    logs = logs_repo.list_logs_by_media_upload(media_upload_id)
    return VideoJobStatusResponse(
        media_upload_id=media_upload_id,
        status=upload["status"],
        result_log_ids=[log["id"] for log in logs],
    )
