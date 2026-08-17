from datetime import datetime

from pydantic import BaseModel


class ReportGenerateRequest(BaseModel):
    period_start: datetime
    period_end: datetime


class ReportResponse(BaseModel):
    id: int
    period_start: datetime
    period_end: datetime
    summary_text: str
    generated_at: datetime
