from datetime import datetime

from pydantic import BaseModel


class RecognitionResult(BaseModel):
    decision: str
    user_id: int | None
    full_name: str | None
    confidence_score: float
    liveness_passed: bool | None
    log_id: int


class AccessLogResponse(BaseModel):
    id: int
    user_id: int | None
    media_upload_id: int | None
    camera_id: str | None
    event_timestamp: datetime
    confidence_score: float
    liveness_passed: bool | None
    decision: str
    snapshot_path: str | None


class VideoJobResponse(BaseModel):
    media_upload_id: int
    status: str


class VideoJobStatusResponse(BaseModel):
    media_upload_id: int
    status: str
    result_log_ids: list[int] = []
