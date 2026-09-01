from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
)

from PySide6.QtCore import Qt
from app.theme import *

# ============================================
# Individual Action Card
# ============================================


class ActionCard(QPushButton):

    def __init__(self, icon, title, subtitle="", primary=False):
        super().__init__()

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(95)

        if primary:

            bg = """
                QPushButton{
                    background:qlineargradient(
                        x1:0,y1:0,
                        x2:1,y2:0,
                        stop:0 #2563EB,
                        stop:1 #5A8DEE
                    );
                    border:none;
                    border-radius:18px;
                }

                QPushButton:hover{
                    background:#3B82F6;
                }

                QPushButton:pressed{
                    background:#1D4ED8;
                }
            """

        else:

            bg = """
                QPushButton{
                    background:#182235;
                    border:1px solid #2B3B5A;
                    border-radius:18px;
                }

                QPushButton:hover{
                    background:#22304A;
                    border:1px solid #3B82F6;
                }

                QPushButton:pressed{
                    background:#162033;
                }
            """

        self.setStyleSheet(bg)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(18)

        # ---------------- Icon ----------------

        iconLabel = QLabel(icon)

        iconLabel.setAlignment(Qt.AlignCenter)

        iconLabel.setStyleSheet("""
            font-size:28px;
        """)

        # ---------------- Text ----------------

        textLayout = QVBoxLayout()
        textLayout.setSpacing(2)

        titleLabel = QLabel(title)

        titleLabel.setStyleSheet(f"""
            color:{TEXT};
            font-size:19px;
            font-weight:700;
        """)

        subtitleLabel = QLabel(subtitle)

        subtitleLabel.setStyleSheet(f"""
            color:{SECONDARY};
            font-size:12px;
        """)

        textLayout.addWidget(titleLabel)
        textLayout.addWidget(subtitleLabel)

        layout.addWidget(iconLabel)
        layout.addLayout(textLayout)
        layout.addStretch()


# ============================================
# Quick Actions Row
# ============================================


class QuickActions(QWidget):

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)

        layout.setSpacing(22)
        layout.setContentsMargins(0, 0, 0, 0)

        importBtn = ActionCard("⬆️", "Import Video", "MP4 • MOV • MKV", primary=True)

        recentBtn = ActionCard("🕒", "Open Recent", "Continue editing")

        layout.addWidget(importBtn)
        layout.addWidget(recentBtn)

        layout.setStretch(0, 1)
        layout.setStretch(1, 1)
