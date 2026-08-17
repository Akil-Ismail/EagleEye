from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QFileDialog, QLabel, QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget

from app.api_client import ApiClient, ApiError

POLL_INTERVAL_MS = 2000


class UploadPanel(QWidget):
    def __init__(self, client: ApiClient):
        super().__init__()
        self.client = client
        self.poll_timer: QTimer | None = None

        image_button = QPushButton("Upload Image for Recognition…")
        image_button.clicked.connect(self._upload_image)

        video_button = QPushButton("Upload Video for Recognition…")
        video_button.clicked.connect(self._upload_video)

        self.status_label = QLabel("No upload in progress.")
        self.result_view = QTextEdit()
        self.result_view.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addWidget(image_button)
        layout.addWidget(video_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.result_view)

    def _upload_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.jpg *.jpeg *.png)")
        if not path:
            return

        with open(path, "rb") as handle:
            image_bytes = handle.read()

        try:
            results = self.client.recognize_frame(image_bytes, camera_id="upload")
        except ApiError as exc:
            QMessageBox.critical(self, "Recognition failed", str(exc))
            return

        self.status_label.setText(f"Processed {Path(path).name} — {len(results)} face(s) detected")
        self.result_view.setPlainText(
            "\n\n".join(
                f"Decision: {result['decision']}\n"
                f"Matched user: {result.get('full_name') or 'Unknown'}\n"
                f"Confidence: {result['confidence_score']:.2f}\n"
                f"Liveness: {result['liveness_passed']}\n"
                f"Log ID: {result['log_id']}"
                for result in results
            )
        )

    def _upload_video(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Videos (*.mp4 *.avi *.mov *.mkv)")
        if not path:
            return

        try:
            job = self.client.recognize_video(path)
        except ApiError as exc:
            QMessageBox.critical(self, "Upload failed", str(exc))
            return

        self.status_label.setText(f"Processing {Path(path).name} (job #{job['media_upload_id']})…")
        self.result_view.clear()

        if self.poll_timer is not None:
            self.poll_timer.stop()

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(lambda: self._poll_job(job["media_upload_id"]))
        self.poll_timer.start(POLL_INTERVAL_MS)

    def _poll_job(self, media_upload_id: int) -> None:
        try:
            status = self.client.video_job_status(media_upload_id)
        except ApiError as exc:
            self.status_label.setText(f"Failed to check job status: {exc}")
            self.poll_timer.stop()
            return

        if status["status"] in ("completed", "failed"):
            self.poll_timer.stop()
            self.status_label.setText(f"Job #{media_upload_id} {status['status']}")
            self.result_view.setPlainText(
                f"Status: {status['status']}\nRecognition events recorded: {len(status['result_log_ids'])}\n"
                f"Log IDs: {status['result_log_ids']}"
            )
        else:
            self.status_label.setText(f"Job #{media_upload_id} still {status['status']}…")
