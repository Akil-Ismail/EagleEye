import json

import requests

from app.core.config import get_settings

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = (
    "You are a security analyst assistant for a face-recognition access control system. "
    "Summarize the given access log and alert records into a concise, readable incident report "
    "for a human administrator. Entries with an 'occurrences' field represent a run of "
    "consecutive, identical events collapsed into one — treat each such entry as a single "
    "continuous incident, not separate ones. Call out unauthorized access attempts, "
    "suspected spoofing, and any repeated unknown visitors. Base the report only on the data "
    "given, do not invent details."
)


def summarize_events(log_rows: list[dict], alert_rows: list[dict]) -> str:
    settings = get_settings()
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")

    response = requests.post(
        GROQ_API_URL,
        headers={"Authorization": f"Bearer {settings.groq_api_key}"},
        json={
            "model": settings.groq_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _format_events(log_rows, alert_rows)},
            ],
            "temperature": 0.3,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def _collapse_logs(log_rows: list[dict]) -> list[dict]:
    """Collapse consecutive same user/decision/camera rows so a continuously-recognized
    face doesn't turn into hundreds of near-identical lines in the LLM prompt."""
    chronological = sorted(log_rows, key=lambda row: row["event_timestamp"])

    runs: list[dict] = []
    for row in chronological:
        key = (row["user_id"], row["decision"], row["camera_id"])
        if runs and runs[-1]["_key"] == key:
            run = runs[-1]
            run["occurrences"] += 1
            run["last_seen"] = row["event_timestamp"]
            run["_confidence_sum"] += row["confidence_score"]
        else:
            runs.append(
                {
                    "_key": key,
                    "user_id": row["user_id"],
                    "decision": row["decision"],
                    "camera_id": row["camera_id"],
                    "first_seen": row["event_timestamp"],
                    "last_seen": row["event_timestamp"],
                    "occurrences": 1,
                    "_confidence_sum": row["confidence_score"],
                }
            )

    for run in runs:
        run["avg_confidence"] = round(run.pop("_confidence_sum") / run["occurrences"], 3)
        del run["_key"]
    return runs


def _collapse_alerts(alert_rows: list[dict]) -> list[dict]:
    """Collapse consecutive same-type alerts the same way as logs, since the recognition
    service raises one alert per unresolved poll rather than once per incident."""
    chronological = sorted(alert_rows, key=lambda row: row["created_at"])

    runs: list[dict] = []
    for row in chronological:
        if runs and runs[-1]["type"] == row["type"]:
            run = runs[-1]
            run["occurrences"] += 1
            run["last_seen"] = row["created_at"]
            run["resolved_count"] += 1 if row["resolved"] else 0
        else:
            runs.append(
                {
                    "type": row["type"],
                    "first_seen": row["created_at"],
                    "last_seen": row["created_at"],
                    "occurrences": 1,
                    "resolved_count": 1 if row["resolved"] else 0,
                }
            )
    return runs


def _format_events(log_rows: list[dict], alert_rows: list[dict]) -> str:
    return json.dumps(
        {"access_logs": _collapse_logs(log_rows), "alerts": _collapse_alerts(alert_rows)},
        default=str,
    )
