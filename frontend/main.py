import sys

from PyQt6.QtWidgets import QApplication

from app.api_client import ApiClient
from app.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    client = ApiClient()
    window = MainWindow(client)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
