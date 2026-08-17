import time

import cv2
import requests
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage

from app.api_client import ApiClient, ApiError

RECOGNIZE_INTERVAL_SECONDS = 2.0
MAX_CONSECUTIVE_READ_FAILURES = 30


class CameraWorker(QThread):
    frame_ready = pyqtSignal(QImage)
    recognition_results = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, client: ApiClient, camera_index: int = 0, camera_id: str = "webcam-0", enable_recognition: bool = True):
        super().__init__()
        self.client = client
        self.camera_index = camera_index
        self.camera_id = camera_id
        self.enable_recognition = enable_recognition
        self._running = False

    def run(self):
        capture = cv2.VideoCapture(self.camera_index)
        if not capture.isOpened():
            self.error.emit(f"Could not open camera {self.camera_index}")
            return

        self._running = True
        last_recognize = 0.0
        consecutive_failures = 0

        while self._running:
            ok, frame = capture.read()
            if not ok:
                consecutive_failures += 1
                if consecutive_failures >= MAX_CONSECUTIVE_READ_FAILURES:
                    self.error.emit("Camera stopped responding")
                    break
                time.sleep(0.1)
                continue
            consecutive_failures = 0

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channels = rgb_frame.shape
            image = QImage(rgb_frame.data, width, height, channels * width, QImage.Format.Format_RGB888)
            self.frame_ready.emit(image.copy())

            now = time.monotonic()
            if self.enable_recognition and now - last_recognize >= RECOGNIZE_INTERVAL_SECONDS:
                last_recognize = now
                self._try_recognize(frame)

        capture.release()

    def _try_recognize(self, frame) -> None:
        _, buffer = cv2.imencode(".jpg", frame)
        try:
            results = self.client.recognize_frame(buffer.tobytes(), camera_id=self.camera_id)
            self.recognition_results.emit(results)
        except ApiError as exc:
            self.error.emit(str(exc))
        except (requests.ConnectionError, requests.Timeout) as exc:
            self.error.emit(f"Recognition request failed: {exc}")

    def stop(self) -> None:
        self._running = False
        self.wait()
