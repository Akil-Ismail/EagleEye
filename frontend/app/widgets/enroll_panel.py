from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.api_client import ApiClient, ApiError
from app.widgets.capture_dialog import CaptureDialog


class EnrollPanel(QWidget):
    def __init__(self, client: ApiClient, on_enrolled=None):
        super().__init__()
        self.client = client
        self.on_enrolled = on_enrolled
        self.captured_photos: list[bytes] = []
        self.uploaded_paths: list[str] = []

        self.name_input = QLineEdit()
        self.role_input = QLineEdit()
        self.notes_input = QTextEdit()
        self.notes_input.setFixedHeight(60)

        form = QFormLayout()
        form.addRow("Full name", self.name_input)
        form.addRow("Role", self.role_input)
        form.addRow("Notes", self.notes_input)

        self.photo_list = QListWidget()

        capture_button = QPushButton("Capture from Camera…")
        capture_button.clicked.connect(self._open_capture_dialog)
        upload_button = QPushButton("Add Photo Files…")
        upload_button.clicked.connect(self._pick_files)
        clear_button = QPushButton("Clear Photos")
        clear_button.clicked.connect(self._clear_photos)

        photo_controls = QHBoxLayout()
        photo_controls.addWidget(capture_button)
        photo_controls.addWidget(upload_button)
        photo_controls.addWidget(clear_button)

        enroll_button = QPushButton("Enroll User")
        enroll_button.clicked.connect(self._enroll)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(photo_controls)
        layout.addWidget(self.photo_list)
        layout.addWidget(enroll_button)

    def _open_capture_dialog(self) -> None:
        dialog = CaptureDialog(self.client)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            for data in dialog.captured_frames:
                self.captured_photos.append(data)
                self.photo_list.addItem(f"camera-capture-{len(self.captured_photos)}.jpg")

    def _pick_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Photos", "", "Images (*.jpg *.jpeg *.png)")
        for path in paths:
            self.uploaded_paths.append(path)
            self.photo_list.addItem(Path(path).name)

    def _clear_photos(self) -> None:
        self.captured_photos.clear()
        self.uploaded_paths.clear()
        self.photo_list.clear()

    def _enroll(self) -> None:
        full_name = self.name_input.text().strip()
        if not full_name:
            QMessageBox.warning(self, "Missing name", "Full name is required.")
            return
        if not self.captured_photos and not self.uploaded_paths:
            QMessageBox.warning(self, "No photos", "Add at least one enrollment photo.")
            return

        try:
            user = self.client.enroll(
                full_name=full_name,
                role=self.role_input.text().strip() or None,
                notes=self.notes_input.toPlainText().strip() or None,
                captured_photos=self.captured_photos,
                uploaded_paths=self.uploaded_paths,
            )
        except ApiError as exc:
            QMessageBox.critical(self, "Enrollment failed", str(exc))
            return

        QMessageBox.information(self, "Enrolled", f"Enrolled {user['full_name']} (id {user['id']})")
        self.name_input.clear()
        self.role_input.clear()
        self.notes_input.clear()
        self._clear_photos()
        if self.on_enrolled:
            self.on_enrolled()
