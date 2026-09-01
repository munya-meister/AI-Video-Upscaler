from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QGraphicsDropShadowEffect,
)

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from app.theme import *


class StatsCard(QFrame):

    def __init__(self, title, value, icon):
        super().__init__()

        self.setFixedSize(220, 120)

        self.setObjectName("card")

        self.setStyleSheet(f"""
            QFrame#card{{
                background:{PANEL};
                border-radius:18px;
                border:1px solid rgba(59,130,246,40);
            }}

            QLabel{{
                border:none;
                background:transparent;
            }}
        """)

        shadow = QGraphicsDropShadowEffect()

        shadow.setBlurRadius(35)
        shadow.setOffset(0)
        shadow.setColor(QColor(59, 130, 246, 90))

        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(20, 20, 20, 20)

        layout.setSpacing(6)

        iconLabel = QLabel(icon)

        iconLabel.setAlignment(Qt.AlignLeft)

        iconLabel.setStyleSheet(f"""
            font-size:28px;
            background:transparent;
            border:none;
        """)

        titleLabel = QLabel(title)

        titleLabel.setStyleSheet(f"""
            color:{SECONDARY};
            font-size:13px;
            background:transparent;
            border:none;
        """)

        valueLabel = QLabel(str(value))

        valueLabel.setStyleSheet(f"""
            color:{TEXT};
            font-size:34px;
            font-weight:700;
            background:transparent;
            border:none;
        """)

        layout.addWidget(iconLabel)
        layout.addWidget(titleLabel)
        layout.addWidget(valueLabel)
