from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout,
)

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont

from app.theme import *


class TitleBar(QWidget):

    def __init__(self, window):
        super().__init__()

        self.window = window
        self.dragPos = QPoint()

        self.setObjectName("TitleBar")
        self.setFixedHeight(52)

        self.setStyleSheet(f"""
        QWidget#TitleBar {{
            background:{SIDEBAR};
            border-bottom:1px solid rgba(59,130,246,60);
        }}

        QLabel {{
            background:transparent;
            color:{TEXT};
            font-size:16px;
            font-weight:700;
            border:none;
        }}

        QPushButton {{
            background:transparent;
            color:{TEXT};
            border:none;
            font-size:16px;
            min-width:42px;
            border-radius:8px;
        }}

        QPushButton:hover {{
            background:rgba(59,130,246,.18);
        }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 12, 0)

        logo = QLabel("VIDEL")
        logo.setFont(QFont("Segoe UI", 11, QFont.Bold))

        layout.addWidget(logo)
        layout.addStretch()

        self.minBtn = QPushButton("—")
        self.maxBtn = QPushButton("□")
        self.closeBtn = QPushButton("✕")

        self.closeBtn.setStyleSheet("""
        QPushButton{
            background:transparent;
            color:white;
            border:none;
            border-radius:8px;
        }

        QPushButton:hover{
            background:#EF4444;
        }
        """)

        layout.addWidget(self.minBtn)
        layout.addWidget(self.maxBtn)
        layout.addWidget(self.closeBtn)

        self.minBtn.clicked.connect(window.showMinimized)
        self.maxBtn.clicked.connect(self.toggleMaxRestore)
        self.closeBtn.clicked.connect(window.close)

    def toggleMaxRestore(self):

        if self.window.isMaximized():
            self.window.showNormal()
        else:
            self.window.showMaximized()

    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:
            self.dragPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):

        if event.buttons() == Qt.LeftButton:
            self.window.move(
                self.window.pos() + event.globalPosition().toPoint() - self.dragPos
            )

            self.dragPos = event.globalPosition().toPoint()
