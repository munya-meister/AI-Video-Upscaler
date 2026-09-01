from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
)

from PySide6.QtCore import Qt
from app.theme import *


class TopBar(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedHeight(72)

        layout = QHBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        # -------------------------
        # Left
        # -------------------------

    

        # -------------------------
        # Search
        # -------------------------

        search = QLineEdit()

        search.setPlaceholderText("Search projects...")

        search.setFixedSize(280, 42)

        search.setStyleSheet(f"""
        QLineEdit{{
            background:{CARD};
            border:1px solid {BORDER};
            border-radius:20px;
            padding-left:18px;
            color:{TEXT};
            font-size:14px;
        }}

        QLineEdit:focus{{
            border:1px solid {ACCENT};
        }}
        """)

        layout.addWidget(search)

        # -------------------------
        # Notification
        # -------------------------

        bell = QPushButton("🔔")

        bell.setFixedSize(46, 46)

        bell.setCursor(Qt.PointingHandCursor)

        bell.setStyleSheet(f"""
        QPushButton{{
            background:{CARD};
            border:1px solid {BORDER};
            border-radius:23px;
            font-size:18px;
        }}

        QPushButton:hover{{
            background:{CARD_HOVER};
        }}
        """)

        layout.addWidget(bell)

        # -------------------------
        # Sync
        # -------------------------

        sync = QPushButton("⟳")

        sync.setFixedSize(46, 46)

        sync.setCursor(Qt.PointingHandCursor)

        sync.setStyleSheet(bell.styleSheet())

        layout.addWidget(sync)

        # -------------------------
        # Avatar
        # -------------------------

        avatar = QPushButton("M")

        avatar.setFixedSize(46, 46)

        avatar.setCursor(Qt.PointingHandCursor)

        avatar.setStyleSheet(f"""
        QPushButton{{
            background:qlineargradient(
                x1:0,y1:0,
                x2:1,y2:1,
                stop:0 {ACCENT},
                stop:1 {ACCENT_DARK}
            );
            color:{TEXT};
            font-size:18px;
            font-weight:700;
            border:none;
            border-radius:23px;
        }}

        QPushButton:hover{{
            background:{ACCENT_HOVER};
        }}
        """)

        layout.addWidget(avatar)
