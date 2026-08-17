from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout

from app.api_client import ApiClient
from app.image_utils import qimage_to_jpeg_bytes
from app.widgets.camera_worker import CameraWorker


class CaptureDialog(QDialog):
    def __init__(self, client: ApiClient):
        super().__init__()
        self.setWindowTitle("Capture Enrollment Photos")
        self.captured_frames: list[bytes] = []
        self._last_frame: QImage | None = None

        self.video_label = QLabel("Starting camera…")
        self.video_label.setMinimumSize(480, 360)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; color: white;")
        self.count_label = QLabel("Captured: 0")

        capture_button = QPushButton("Capture Photo")
        capture_button.clicked.connect(self._capture)
        done_button = QPushButton("Done")
        done_button.clicked.connect(self.accept)

        controls = QHBoxLayout()
        controls.addWidget(capture_button)
        controls.addWidget(done_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.video_label)
        layout.addWidget(self.count_label)
        layout.addLayout(controls)

        self.worker = CameraWorker(client, enable_recognition=False)
        self.worker.frame_ready.connect(self._display_frame)
        self.worker.error.connect(lambda message: QMessageBox.warning(self, "Camera error", message))
        self.worker.start()

    def _display_frame(self, image: QImage) -> None:
        self._last_frame = image
        pixmap = QPixmap.fromImage(image).scaled(
            self.video_label.width(), self.video_label.height(), Qt.AspectRatioMode.KeepAspectRatio
        )
        self.video_label.setPixmap(pixmap)

    def _capture(self) -> None:
        if self._last_frame is None:
            return
        self.captured_frames.append(qimage_to_jpeg_bytes(self._last_frame))
        self.count_label.setText(f"Captured: {len(self.captured_frames)}")

    def accept(self) -> None:
        self.worker.stop()
        super().accept()

    def reject(self) -> None:
        self.worker.stop()
        super().reject()
