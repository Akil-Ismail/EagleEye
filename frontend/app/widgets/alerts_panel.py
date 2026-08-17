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
STATUS_FILTERS = ["Unresolved", "Resolved", "All"]
COLUMNS = ["ID", "Log ID", "Type", "Resolved", "Created At", "Action"]


class AlertsPanel(QWidget):
    def __init__(self, client: ApiClient):
        super().__init__()
        self.client = client

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(STATUS_FILTERS)
        self.filter_combo.currentIndexChanged.connect(self.refresh)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Status:"))
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

    def _resolved_filter(self) -> bool | None:
        choice = self.filter_combo.currentText()
        return {"Unresolved": False, "Resolved": True, "All": None}[choice]

    def refresh(self) -> None:
        try:
            alerts = self.client.list_alerts(resolved=self._resolved_filter())
        except ApiError as exc:
            QMessageBox.warning(self, "Failed to load alerts", str(exc))
            return

        self.table.setRowCount(len(alerts))
        for row, alert in enumerate(alerts):
            values = [str(alert["id"]), str(alert["log_id"]), alert["type"], str(alert["resolved"]), alert["created_at"]]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))

            resolve_button = QPushButton("Resolve")
            resolve_button.setEnabled(not alert["resolved"])
            resolve_button.clicked.connect(lambda _checked, alert_id=alert["id"]: self._resolve(alert_id))
            self.table.setCellWidget(row, len(values), resolve_button)

    def _resolve(self, alert_id: int) -> None:
        try:
            self.client.resolve_alert(alert_id)
        except ApiError as exc:
            QMessageBox.critical(self, "Failed to resolve alert", str(exc))
            return
        self.refresh()
