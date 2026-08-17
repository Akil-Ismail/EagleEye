import requests
from fastapi import APIRouter, HTTPException

from app.db.repository import alerts_repo, logs_repo, reports_repo
from app.schemas.reports import ReportGenerateRequest, ReportResponse
from app.services.groq_service import summarize_events

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=list[ReportResponse])
def list_reports(limit: int = 50, offset: int = 0):
    return reports_repo.list_reports(limit=limit, offset=offset)


@router.post("/generate", response_model=ReportResponse)
def generate_report(request: ReportGenerateRequest):
    period_start = request.period_start.isoformat()
    period_end = request.period_end.isoformat()
    logs = logs_repo.list_logs_between(period_start, period_end)
    alerts = alerts_repo.list_alerts_between(period_start, period_end)

    try:
        summary_text = summarize_events(logs, alerts)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Groq request failed: {exc}") from exc

    report_id = reports_repo.create_report(
        period_start=request.period_start,
        period_end=request.period_end,
        summary_text=summary_text,
        log_ids_included=[log["id"] for log in logs],
    )
    return reports_repo.get_report(report_id)
