from fastapi import APIRouter

from app.db.repository import alerts_repo
from app.schemas.alerts import AlertResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
def list_alerts(resolved: bool | None = None, limit: int = 100, offset: int = 0):
    return alerts_repo.list_alerts(resolved=resolved, limit=limit, offset=offset)


@router.patch("/{alert_id}/resolve")
def resolve_alert(alert_id: int):
    alerts_repo.resolve_alert(alert_id)
    return {"status": "resolved"}
