from PyQt6.QtCore import QDateTime, Qt
from PyQt6.QtWidgets import (
    QDateTimeEdit,
    QFormLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.api_client import ApiClient, ApiError


class ReportsPanel(QWidget):
    def __init__(self, client: ApiClient):
        super().__init__()
        self.client = client

        now = QDateTime.currentDateTime()
        self.start_input = QDateTimeEdit(now.addSecs(-24 * 3600))
        self.start_input.setCalendarPopup(True)
        self.end_input = QDateTimeEdit(now)
        self.end_input.setCalendarPopup(True)

        form = QFormLayout()
        form.addRow("Period start", self.start_input)
        form.addRow("Period end", self.end_input)

        generate_button = QPushButton("Generate Report")
        generate_button.clicked.connect(self._generate)
        refresh_button = QPushButton("Refresh History")
        refresh_button.clicked.connect(self.refresh)

        buttons = QHBoxLayout()
        buttons.addWidget(generate_button)
        buttons.addWidget(refresh_button)

        self.history_list = QListWidget()
        self.history_list.currentItemChanged.connect(self._show_selected)

        self.summary_view = QTextEdit()
        self.summary_view.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addWidget(self.history_list)
        layout.addWidget(self.summary_view)

        self.refresh()

    def _generate(self) -> None:
        period_start = self.start_input.dateTime().toString(Qt.DateFormat.ISODate)
        period_end = self.end_input.dateTime().toString(Qt.DateFormat.ISODate)
        try:
            report = self.client.generate_report(period_start, period_end)
        except ApiError as exc:
            QMessageBox.critical(self, "Report generation failed", str(exc))
            return
        self.summary_view.setPlainText(report["summary_text"])
        self.refresh()

    def refresh(self) -> None:
        try:
            reports = self.client.list_reports()
        except ApiError as exc:
            QMessageBox.warning(self, "Failed to load reports", str(exc))
            return

        self.history_list.clear()
        for report in reports:
            item = QListWidgetItem(f"#{report['id']} — {report['period_start']} to {report['period_end']}")
            item.setData(Qt.ItemDataRole.UserRole, report)
            self.history_list.addItem(item)

    def _show_selected(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        report = current.data(Qt.ItemDataRole.UserRole)
        self.summary_view.setPlainText(report["summary_text"])
