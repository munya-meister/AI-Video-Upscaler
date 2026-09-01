from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QScrollArea,
)

from PySide6.QtCore import Qt
from app.theme import *
from app.services.project_service import project_service
from app.recent_projects import row_for_project


class ProjectsPage(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName("ProjectsPage")

        self.setStyleSheet(f"""
        QWidget#ProjectsPage {{
            background: {BACKGROUND};
        }}
        """)

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

        container = QWidget()
        container.setStyleSheet(f"""
        background:{BACKGROUND};
        """)

        content = QVBoxLayout(container)
        content.setContentsMargins(55, 35, 55, 35)
        content.setSpacing(16)

        title = QLabel("Projects")
        title.setStyleSheet(f"""
            color:{TEXT};
            font-size:24px;
            font-weight:700;
            background:transparent;
            border:none;
        """)

        content.addWidget(title)

        self.list_layout = QVBoxLayout()
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(16)
        content.addLayout(self.list_layout)

        content.addStretch()

        scroll.setWidget(container)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        self.refresh()

    def showEvent(self, event):
        self.refresh()
        super().showEvent(event)

    def refresh(self):
        """Rebuild rows from the shared project service list."""
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for project in project_service.get_projects():
            self.list_layout.addWidget(row_for_project(project))
