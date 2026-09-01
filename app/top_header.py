from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
)

from PySide6.QtCore import Qt, QDate
from app.theme import *


class TopHeader(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedHeight(95)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # =====================================
        # LEFT SIDE
        # =====================================

        left = QVBoxLayout()
        left.setSpacing(4)

        greeting = QLabel("Good Evening, Munyaradzi 👋")

        greeting.setStyleSheet(f"""
            color:{TEXT};
            font-size:30px;
            font-weight:700;
            background:transparent;
            border:none;
        """)

        subtitle = QLabel("Continue enhancing your latest masterpiece.")

        subtitle.setStyleSheet(f"""
            color:{SECONDARY};
            font-size:15px;
            background:transparent;
            border:none;
        """)

        current_date = QDate.currentDate()
        date_string = current_date.toString("dddd • d MMMM yyyy")
        date = QLabel(date_string)

        date.setStyleSheet(f"""
            color:{MUTED};
            font-size:12px;
            background:transparent;
            border:none;
        """)

        left.addWidget(greeting)
        left.addWidget(subtitle)
        left.addWidget(date)

        layout.addLayout(left)

        layout.addStretch()

        # =====================================
        # RIGHT SIDE
        # =====================================

        stats = QVBoxLayout()
        stats.setSpacing(4)

        label = QLabel("Today's Activity")

        label.setAlignment(Qt.AlignRight)

        label.setStyleSheet(f"""
            color:{MUTED};
            font-size:12px;
            background:transparent;
            border:none;
        """)

        value = QLabel("3 Projects • 1 Export")

        value.setAlignment(Qt.AlignRight)

        value.setStyleSheet(f"""
            color:{TEXT};
            font-size:18px;
            font-weight:700;
            background:transparent;
            border:none;
        """)

        stats.addWidget(label)
        stats.addWidget(value)

        layout.addLayout(stats)

