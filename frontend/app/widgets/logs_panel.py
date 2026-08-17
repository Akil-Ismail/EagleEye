from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.api_client import ApiClient, ApiError

REFRESH_INTERVAL_MS = 5000
DECISION_FILTERS = ["All", "authorized", "unknown", "spoof_suspected"]
COLUMNS = ["ID", "Timestamp", "Decision", "User ID", "Confidence", "Liveness", "Camera / Upload"]


class LogsPanel(QWidget):
    def __init__(self, client: ApiClient):
        super().__init__()
        self.client = client

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(DECISION_FILTERS)
        self.filter_combo.currentIndexChanged.connect(self.refresh)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Decision:"))
        controls.addWidget(self.filter_combo)
        controls.addWidget(refresh_button)
        controls.addStretch()

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.table)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(REFRESH_INTERVAL_MS)

    def refresh(self) -> None:
        decision = self.filter_combo.currentText()
        try:
            logs = self.client.list_logs(decision=None if decision == "All" else decision)
        except ApiError as exc:
            QMessageBox.warning(self, "Failed to load logs", str(exc))
            return

        self.table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            source = log["camera_id"] or (f"upload #{log['media_upload_id']}" if log["media_upload_id"] else "—")
            values = [
                str(log["id"]),
                log["event_timestamp"],
                log["decision"],
                str(log["user_id"]) if log["user_id"] else "—",
                f"{log['confidence_score']:.2f}",
                "—" if log["liveness_passed"] is None else str(log["liveness_passed"]),
                source,
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))
