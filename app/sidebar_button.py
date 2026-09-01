from PySide6.QtWidgets import (
    QPushButton,
    QGraphicsDropShadowEffect,
)

from PySide6.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    QSize,
)

from PySide6.QtGui import QColor
from app.theme import CARD, CARD_HOVER, SECONDARY, TEXT, ACCENT, ACCENT_DARK


class SidebarButton(QPushButton):

    def __init__(self, text="", icon=None):
        super().__init__(text)

        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)

        if icon:
            self.setIcon(icon)
            self.setIconSize(QSize(24, 24))

        self.setFixedHeight(64)

        # Better icon/text alignment
        self.setStyleSheet(f"""
            QPushButton{{
                background:{CARD};
                color:{SECONDARY};
                border:none;
                border-radius:18px;
                text-align:left;
                padding-left:24px;
                spacing:16px;
                font-size:16px;
                font-weight:600;
            }}

            QPushButton:hover{{
                background:{CARD_HOVER};
                color:{TEXT};
            }}

            QPushButton:checked{{
                background:qlineargradient(
                    x1:0,
                    y1:0,
                    x2:1,
                    y2:0,
                    stop:0 {ACCENT_DARK},
                    stop:1 {CARD_HOVER}
                );
                color:{TEXT};
            }}
        """)

        # ------------------------
        # Glow Effect
        # ------------------------

        self.shadow = QGraphicsDropShadowEffect(self)

        self.shadow.setBlurRadius(0)

        self.shadow.setOffset(0)

        self.shadow.setColor(QColor(59, 130, 246))

        self.setGraphicsEffect(self.shadow)

        self.glow = QPropertyAnimation(self.shadow, b"blurRadius")

        self.glow.setDuration(180)

        self.glow.setEasingCurve(QEasingCurve.OutCubic)

    # ------------------------
    # Hover In
    # ------------------------

    def enterEvent(self, event):

        self.glow.stop()

        self.glow.setStartValue(self.shadow.blurRadius())

        self.glow.setEndValue(22)

        self.glow.start()

        super().enterEvent(event)

    # ------------------------
    # Hover Out
    # ------------------------

    def leaveEvent(self, event):

        self.glow.stop()

        self.glow.setStartValue(self.shadow.blurRadius())

        self.glow.setEndValue(0)

        self.glow.start()

        super().leaveEvent(event)
