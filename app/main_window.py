from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
)

from app.sidebar import Sidebar
from app.dashboard import Dashboard
from app.projects import ProjectsPage
from app.enhance import EnhancePage
from app.theme import BACKGROUND


class VidelWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Videl - Video Eloquence")
        self.resize(1400, 800)

        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.sidebar = Sidebar()
        self.dashboard = Dashboard()
        self.projects_page = ProjectsPage()
        self.enhance_page = EnhancePage()

        self.stack = QStackedWidget()
        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.projects_page)
        self.stack.addWidget(self.enhance_page)

        self.sidebar.section_changed.connect(self.show_section)
        self.dashboard.projects_changed.connect(self.projects_page.refresh)
        self.dashboard.projects_changed.connect(self.enhance_page.load_current_project)
        self.enhance_page.projects_changed.connect(self.dashboard.recent_projects.refresh)
        self.enhance_page.projects_changed.connect(self.projects_page.refresh)

        body.addWidget(self.sidebar)
        body.addWidget(self.stack, 1)

        root.addLayout(body)

        self.setStyleSheet(f"""
            QMainWindow {{
                background: {BACKGROUND};
            }}
        """)

    def show_section(self, name):
        if name == "Dashboard":
            self.dashboard.recent_projects.refresh()
            self.stack.setCurrentWidget(self.dashboard)
        elif name == "Projects":
            self.projects_page.refresh()
            self.stack.setCurrentWidget(self.projects_page)
        elif name == "AI Enhance":
            self.enhance_page.load_current_project()
            self.stack.setCurrentWidget(self.enhance_page)
