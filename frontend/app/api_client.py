from pathlib import Path

import requests

from app.config import API_BASE_URL


class ApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class ApiClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")

    @staticmethod
    def _handle(response: requests.Response):
        if not response.ok:
            detail = response.text
            try:
                detail = response.json().get("detail", detail)
            except ValueError:
                pass
            raise ApiError(str(detail), response.status_code)
        return response.json() if response.content else None

    def list_users(self, active_only: bool = True) -> list[dict]:
        response = requests.get(
            f"{self.base_url}/users",
            params={"active_only": active_only},
            timeout=10,
        )
        return self._handle(response)

    def deactivate_user(self, user_id: int) -> None:
        response = requests.patch(f"{self.base_url}/users/{user_id}/deactivate", timeout=10)
        self._handle(response)

    def enroll(
        self,
        full_name: str,
        role: str | None,
        notes: str | None,
        captured_photos: list[bytes],
        uploaded_paths: list[str],
    ) -> dict:
        files = [("photos", (f"capture_{i}.jpg", data, "image/jpeg")) for i, data in enumerate(captured_photos)]
        opened_files = []
        for path in uploaded_paths:
            handle = open(path, "rb")
            opened_files.append(handle)
            files.append(("photos", (Path(path).name, handle, "image/jpeg")))

        data = {"full_name": full_name}
        if role:
            data["role"] = role
        if notes:
            data["notes"] = notes

        try:
            response = requests.post(f"{self.base_url}/enroll", data=data, files=files, timeout=60)
        finally:
            for handle in opened_files:
                handle.close()
        return self._handle(response)

    def recognize_frame(self, image_bytes: bytes, camera_id: str = "webcam-0") -> dict:
        files = {"image": ("frame.jpg", image_bytes, "image/jpeg")}
        response = requests.post(
            f"{self.base_url}/recognize/frame",
            params={"camera_id": camera_id},
            files=files,
            timeout=15,
        )
        return self._handle(response)

    def recognize_video(self, video_path: str) -> dict:
        with open(video_path, "rb") as handle:
            files = {"video": (Path(video_path).name, handle, "video/mp4")}
            response = requests.post(f"{self.base_url}/recognize/video", files=files, timeout=60)
        return self._handle(response)

    def video_job_status(self, media_upload_id: int) -> dict:
        response = requests.get(f"{self.base_url}/recognize/video/{media_upload_id}", timeout=10)
        return self._handle(response)

    def list_logs(self, limit: int = 100, offset: int = 0, decision: str | None = None) -> list[dict]:
        params = {"limit": limit, "offset": offset}
        if decision:
            params["decision"] = decision
        response = requests.get(f"{self.base_url}/logs", params=params, timeout=10)
        return self._handle(response)

    def list_alerts(self, resolved: bool | None = None, limit: int = 100, offset: int = 0) -> list[dict]:
        params = {"limit": limit, "offset": offset}
        if resolved is not None:
            params["resolved"] = resolved
        response = requests.get(f"{self.base_url}/alerts", params=params, timeout=10)
        return self._handle(response)

    def resolve_alert(self, alert_id: int) -> None:
        response = requests.patch(f"{self.base_url}/alerts/{alert_id}/resolve", timeout=10)
        self._handle(response)

    def list_reports(self, limit: int = 50, offset: int = 0) -> list[dict]:
        response = requests.get(f"{self.base_url}/reports", params={"limit": limit, "offset": offset}, timeout=10)
        return self._handle(response)

    def generate_report(self, period_start: str, period_end: str) -> dict:
        response = requests.post(
            f"{self.base_url}/reports/generate",
            json={"period_start": period_start, "period_end": period_end},
            timeout=60,
        )
        return self._handle(response)
