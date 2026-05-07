import sys
from PySide6.QtWidgets import QApplication
from docklite.app import DockLiteWindow
from docklite.styles import APP_STYLE


def main():
    app = QApplication(sys.argv)

    app.setStyleSheet(APP_STYLE)

    window = DockLiteWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()