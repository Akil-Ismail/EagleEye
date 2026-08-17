from fastapi import APIRouter

from app.db.repository import logs_repo
from app.schemas.recognition import AccessLogResponse

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("", response_model=list[AccessLogResponse])
def list_logs(limit: int = 100, offset: int = 0, decision: str | None = None):
    return logs_repo.list_logs(limit=limit, offset=offset, decision=decision)
