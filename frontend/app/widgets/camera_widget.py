from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.api_client import ApiClient
from app.widgets.camera_worker import CameraWorker


class CameraWidget(QWidget):
    def __init__(self, client: ApiClient, on_recognition=None):
        super().__init__()
        self.client = client
        self.on_recognition = on_recognition
        self.worker: CameraWorker | None = None

        self.video_label = QLabel("Camera stopped")
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; color: white;")
        self.status_label = QLabel("")

        self.start_button = QPushButton("Start Camera")
        self.stop_button = QPushButton("Stop Camera")
        self.stop_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_camera)
        self.stop_button.clicked.connect(self.stop_camera)

        controls = QHBoxLayout()
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.video_label)
        layout.addLayout(controls)
        layout.addWidget(self.status_label)

    def start_camera(self) -> None:
        if self.worker is not None:
            return
        self.worker = CameraWorker(self.client)
        self.worker.frame_ready.connect(self._display_frame)
        self.worker.recognition_results.connect(self._handle_recognition)
        self.worker.error.connect(self._handle_error)
        self.worker.finished.connect(self._on_camera_finished)
        self.worker.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_camera(self) -> None:
        if self.worker is not None:
            self.worker.stop()
            self.worker = None
        self.video_label.setText("Camera stopped")
        self.status_label.setText("")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def _on_camera_finished(self) -> None:
        # Fires if the capture loop dies on its own (e.g. camera disconnected). A manual
        # stop_camera() already cleared self.worker, so a stale sender here is a no-op.
        if self.sender() is not self.worker:
            return
        self.worker = None
        self.video_label.setText("Camera stopped")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def _display_frame(self, image) -> None:
        pixmap = QPixmap.fromImage(image).scaled(
            self.video_label.width(), self.video_label.height(), Qt.AspectRatioMode.KeepAspectRatio
        )
        self.video_label.setPixmap(pixmap)

    def _handle_recognition(self, results: list) -> None:
        self.status_label.setStyleSheet("")
        if not results:
            self.status_label.setText("No face detected")
            return

        colors = {"authorized": "lightgreen", "unknown": "orange", "spoof_suspected": "red"}
        lines = []
        for result in results:
            decision = result.get("decision", "unknown")
            name = result.get("full_name") or "Unknown"
            confidence = result.get("confidence_score") or 0.0
            liveness = result.get("liveness_passed")
            liveness_note = "" if liveness is None else (" [LIVE]" if liveness else " [SPOOF?]")
            color = colors.get(decision, "white")
            lines.append(
                f'<span style="color:{color}; font-weight:bold;">'
                f"{decision.upper()}: {name} (confidence {confidence:.2f}){liveness_note}</span>"
            )
        self.status_label.setText("<br>".join(lines))
        if self.on_recognition:
            self.on_recognition(results)

    def _handle_error(self, message: str) -> None:
        self.status_label.setStyleSheet("color: red;")
        self.status_label.setText(f"Error: {message}")

    def closeEvent(self, event) -> None:
        self.stop_camera()
        super().closeEvent(event)
