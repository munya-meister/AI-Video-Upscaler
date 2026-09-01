import sys

from PySide6.QtWidgets import QApplication

from app.main_window import VidelWindow
from app.styles import GLOBAL_STYLE


def main():
    app = QApplication(sys.argv)

    # ==========================================
    # Global Application Style
    # ==========================================

    app.setStyleSheet(GLOBAL_STYLE)

    # ==========================================
    # Main Window
    # ==========================================

    window = VidelWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
