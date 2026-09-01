from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal
from app.theme import *
from app.top_bar import TopBar
from app.top_header import TopHeader
from app.recent_projects import RecentProjects
from app.upload_card import UploadCard
from app.services.project_service import project_service


class Dashboard(QWidget):

    projects_changed = Signal()

    def __init__(self):
        super().__init__()

        # ====================================
        # Dashboard Style
        # ====================================

        self.setObjectName("Dashboard")

        self.setStyleSheet(f"""
        QWidget#Dashboard {{
            background: {BACKGROUND};
        }}
        """)

        # ====================================
        # Scroll Area
        # ====================================

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll.setStyleSheet(f"""
        QScrollArea {{
            border:none;
            background:{BACKGROUND};
        }}

        QScrollArea > QWidget > QWidget {{
            background:{BACKGROUND};
        }}

        QScrollBar:vertical {{
            background:transparent;
            width:10px;
        }}

        QScrollBar::handle:vertical {{
            background:#2A3B5F;
            border-radius:5px;
            min-height:40px;
        }}

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height:0px;
        }}
        """)

        # ====================================
        # Dashboard Content
        # ====================================

        container = QWidget()

        container.setStyleSheet(f"""
        background:{BACKGROUND};
        """)

        content = QVBoxLayout(container)

        content.setContentsMargins(55, 35, 55, 35)
        content.setSpacing(28)

        # ====================================
        # Sections
        # ====================================

        content.addWidget(TopBar())

        content.addWidget(TopHeader())

        upload_card = UploadCard()
        upload_card.file_selected.connect(self.handle_file_selected)
        content.addWidget(upload_card)

        self.recent_projects = RecentProjects()
        content.addWidget(self.recent_projects)

        content.addStretch()

        scroll.setWidget(container)

        # ====================================
        # Main Layout
        # ====================================

        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(scroll)

    def handle_file_selected(self, file_path):
        """Import the selected video, then refresh Recent Projects immediately."""
        project_service.import_video(file_path)
        self.recent_projects.refresh()
        self.projects_changed.emit()
