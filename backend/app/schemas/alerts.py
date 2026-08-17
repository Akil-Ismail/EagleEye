from datetime import datetime

from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: int
    log_id: int
    type: str
    resolved: bool
    created_at: datetime
    resolved_at: datetime | None
