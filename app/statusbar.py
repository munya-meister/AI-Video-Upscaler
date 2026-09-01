from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
)

from app.theme import *


class StatusBar(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName("StatusBar")
        self.setFixedHeight(36)

        self.setStyleSheet(f"""
        QWidget#StatusBar {{
            background:{PANEL};
            border-top:1px solid rgba(59,130,246,60);
        }}

        QLabel {{
            background:transparent;
            color:{SECONDARY};
            border:none;
            padding:8px;
            font-size:12px;
        }}
        """)

        layout = QHBoxLayout(self)

        layout.setContentsMargins(14, 0, 14, 0)

        layout.addWidget(QLabel("Status: Ready"))

        layout.addStretch()

        layout.addWidget(QLabel("GPU: Not Connected"))
