from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.api_client import ApiClient, ApiError

COLUMNS = ["ID", "Full Name", "Role", "Active", "Enrolled At", "Action"]


class UsersPanel(QWidget):
    def __init__(self, client: ApiClient):
        super().__init__()
        self.client = client

        self.active_only_checkbox = QCheckBox("Active only")
        self.active_only_checkbox.setChecked(True)
        self.active_only_checkbox.stateChanged.connect(self.refresh)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)

        controls = QHBoxLayout()
        controls.addWidget(self.active_only_checkbox)
        controls.addWidget(refresh_button)
        controls.addStretch()

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.table)

    def refresh(self) -> None:
        try:
            users = self.client.list_users(active_only=self.active_only_checkbox.isChecked())
        except ApiError as exc:
            QMessageBox.warning(self, "Failed to load users", str(exc))
            return

        self.table.setRowCount(len(users))
        for row, user in enumerate(users):
            values = [
                str(user["id"]),
                user["full_name"],
                user["role"] or "—",
                str(user["is_active"]),
                user["enrolled_at"],
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))

            deactivate_button = QPushButton("Deactivate")
            deactivate_button.setEnabled(user["is_active"])
            deactivate_button.clicked.connect(lambda _checked, user_id=user["id"]: self._deactivate(user_id))
            self.table.setCellWidget(row, len(values), deactivate_button)

    def _deactivate(self, user_id: int) -> None:
        try:
            self.client.deactivate_user(user_id)
        except ApiError as exc:
            QMessageBox.critical(self, "Failed to deactivate user", str(exc))
            return
        self.refresh()
