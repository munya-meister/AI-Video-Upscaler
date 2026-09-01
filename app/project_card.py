from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
)

from PySide6.QtCore import Qt
from app.theme import *


class ProjectCard(QWidget):

    def __init__(self, badge, filename, modified, resolution, model):
        super().__init__()

        self.setObjectName("ProjectCard")
        self.setFixedSize(285, 260)

        self.setStyleSheet(f"""
        QWidget#ProjectCard{{
            background:{CARD};
            border:1px solid {BORDER};
            border-radius:18px;
        }}

        QWidget#ProjectCard:hover{{
            background:{CARD_HOVER};
            border:1px solid {ACCENT};
        }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # ====================================
        # Thumbnail
        # ====================================

        thumb = QLabel()
        thumb.setObjectName("Thumbnail")
        thumb.setFixedHeight(125)

        thumb.setStyleSheet(f"""
        QLabel#Thumbnail{{
            background:qlineargradient(
                x1:0,
                y1:0,
                x2:1,
                y2:1,
                stop:0 #314562,
                stop:1 #1E2C45
            );
            border-radius:12px;
            border:none;
            background:transparent;
        }}
        """)

        badgeLabel = QLabel(badge, thumb)
        badgeLabel.move(12, 12)

        badgeLabel.setStyleSheet(f"""
        QLabel{{
            background:{ACCENT};
            color:{TEXT};
            padding:6px 12px;
            border-radius:10px;
            font-size:11px;
            font-weight:700;
            border:none;
        }}
        """)

        layout.addWidget(thumb)

        # ====================================
        # Title Row
        # ====================================

        titleRow = QHBoxLayout()

        title = QLabel(filename)

        title.setStyleSheet(f"""
            color:{TEXT};
            font-size:17px;
            font-weight:700;
            background:transparent;
            border:none;
        """)

        menu = QPushButton("⋮")

        menu.setCursor(Qt.PointingHandCursor)
        menu.setFixedSize(30, 30)

        menu.setStyleSheet(f"""
        QPushButton{{
            background:transparent;
            border:none;
            color:{MUTED};
            font-size:18px;
        }}

        QPushButton:hover{{
            color:{TEXT};
        }}
        """)

        titleRow.addWidget(title)
        titleRow.addStretch()
        titleRow.addWidget(menu)

        layout.addLayout(titleRow)

        # ====================================
        # Modified
        # ====================================

        info = QLabel(modified)

        info.setStyleSheet(f"""
            color:{SECONDARY};
            font-size:13px;
            background:transparent;
            border:none;
        """)

        layout.addWidget(info)

        layout.addStretch()

        # ====================================
        # Bottom Information
        # ====================================

        bottom = QHBoxLayout()

        # LEFT

        left = QVBoxLayout()

        resLabel = QLabel("RESOLUTION")

        resLabel.setStyleSheet(f"""
            color:{MUTED};
            font-size:11px;
            background:transparent;
            border:none;
        """)

        resolutionLabel = QLabel(resolution)

        resolutionLabel.setStyleSheet(f"""
            color:{TEXT};
            font-size:15px;
            font-weight:700;
            background:transparent;
            border:none;
        """)

        left.addWidget(resLabel)
        left.addWidget(resolutionLabel)

        # RIGHT

        right = QVBoxLayout()

        aiLabel = QLabel("AI MODEL")

        aiLabel.setAlignment(Qt.AlignRight)

        aiLabel.setStyleSheet(f"""
            color:{MUTED};
            font-size:11px;
            background:transparent;
            border:none;
        """)

        modelLabel = QLabel(model)

        modelLabel.setAlignment(Qt.AlignRight)

        modelLabel.setStyleSheet(f"""
            color:{ACCENT};
            font-size:15px;
            font-weight:700;
            background:transparent;
            border:none;
        """)

        right.addWidget(aiLabel)
        right.addWidget(modelLabel)

        bottom.addLayout(left)
        bottom.addStretch()
        bottom.addLayout(right)

        layout.addLayout(bottom)
