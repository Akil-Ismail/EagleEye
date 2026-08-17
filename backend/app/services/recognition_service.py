from app.db.repository import alerts_repo, logs_repo
from app.vector.collections import search_similar_faces

SIMILARITY_THRESHOLD = 0.55
REPEATED_UNKNOWN_WINDOW_MINUTES = 5
REPEATED_UNKNOWN_COUNT_THRESHOLD = 3


def match_embedding(embedding: list[float]) -> tuple[int | None, float]:
    matches = search_similar_faces(embedding, top_k=1, score_threshold=SIMILARITY_THRESHOLD)
    if not matches:
        return None, 0.0
    best = matches[0]
    return best.payload["user_id"], best.score


def record_recognition_event(
    user_id: int | None,
    confidence_score: float,
    liveness_passed: bool | None,
    camera_id: str | None = None,
    media_upload_id: int | None = None,
    frame_timestamp_ms: int | None = None,
    snapshot_path: str | None = None,
) -> tuple[int, str]:
    if liveness_passed is False:
        decision = "spoof_suspected"
    elif user_id is not None:
        decision = "authorized"
    else:
        decision = "unknown"

    log_id = logs_repo.create_access_log(
        confidence_score=confidence_score,
        decision=decision,
        user_id=user_id,
        media_upload_id=media_upload_id,
        camera_id=camera_id,
        frame_timestamp_ms=frame_timestamp_ms,
        liveness_passed=liveness_passed,
        snapshot_path=snapshot_path,
    )

    if decision == "spoof_suspected":
        alerts_repo.create_alert(log_id, "spoof_attempt")
    elif decision == "unknown":
        recent_unknown = logs_repo.count_recent_unknown(
            user_id_is_null=True, within_minutes=REPEATED_UNKNOWN_WINDOW_MINUTES
        )
        if recent_unknown >= REPEATED_UNKNOWN_COUNT_THRESHOLD:
            alerts_repo.create_alert(log_id, "repeated_unknown")
        else:
            alerts_repo.create_alert(log_id, "unauthorized_access")

    return log_id, decision
