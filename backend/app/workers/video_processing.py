import cv2

from app.db.repository import media_repo
from app.services.face_service import detect_faces
from app.services.recognition_service import match_embedding, record_recognition_event

FRAME_SAMPLE_INTERVAL = 10


def process_video_job(media_upload_id: int) -> None:
    media_repo.set_status(media_upload_id, "processing")
    upload = media_repo.get_media_upload(media_upload_id)

    try:
        capture = cv2.VideoCapture(upload["file_path"])
        fps = capture.get(cv2.CAP_PROP_FPS) or 30
        frame_index = 0

        while True:
            ok, frame = capture.read()
            if not ok:
                break

            if frame_index % FRAME_SAMPLE_INTERVAL == 0:
                _, buffer = cv2.imencode(".jpg", frame)
                try:
                    faces = detect_faces(buffer.tobytes())
                except ValueError:
                    frame_index += 1
                    continue

                for face in faces:
                    user_id, confidence_score = match_embedding(face["embedding"])
                    record_recognition_event(
                        user_id=user_id,
                        confidence_score=confidence_score,
                        liveness_passed=face["is_live"],
                        media_upload_id=media_upload_id,
                        frame_timestamp_ms=int((frame_index / fps) * 1000),
                    )

            frame_index += 1

        capture.release()
        media_repo.set_status(media_upload_id, "completed", processed_at_now=True)
    except Exception:
        media_repo.set_status(media_upload_id, "failed", processed_at_now=True)
        raise
