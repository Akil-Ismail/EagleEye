from PyQt6.QtWidgets import QMainWindow, QTabWidget

from app.api_client import ApiClient
from app.widgets.alerts_panel import AlertsPanel
from app.widgets.camera_widget import CameraWidget
from app.widgets.enroll_panel import EnrollPanel
from app.widgets.logs_panel import LogsPanel
from app.widgets.reports_panel import ReportsPanel
from app.widgets.upload_panel import UploadPanel
from app.widgets.users_panel import UsersPanel


class MainWindow(QMainWindow):
    def __init__(self, client: ApiClient):
        super().__init__()
        self.client = client
        self.setWindowTitle("EagleEye — Security Dashboard")
        self.resize(1000, 700)

        self.users_panel = UsersPanel(client)
        self.logs_panel = LogsPanel(client)
        self.alerts_panel = AlertsPanel(client)

        tabs = QTabWidget()
        tabs.addTab(CameraWidget(client, on_recognition=lambda _result: self._refresh_activity()), "Live Camera")
        tabs.addTab(EnrollPanel(client, on_enrolled=self.users_panel.refresh), "Enroll User")
        tabs.addTab(UploadPanel(client), "Upload & Recognize")
        tabs.addTab(self.users_panel, "Users")
        tabs.addTab(self.logs_panel, "Access Logs")
        tabs.addTab(self.alerts_panel, "Alerts")
        tabs.addTab(ReportsPanel(client), "Reports")

        self.setCentralWidget(tabs)
        self.users_panel.refresh()
        self.logs_panel.refresh()
        self.alerts_panel.refresh()

    def _refresh_activity(self) -> None:
        self.logs_panel.refresh()
        self.alerts_panel.refresh()

    def closeEvent(self, event) -> None:
        for widget in self.findChildren(CameraWidget):
            widget.stop_camera()
        super().closeEvent(event)
