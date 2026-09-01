from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFrame,
)

from datetime import datetime

from PySide6.QtCore import Qt
from app.theme import *
from app.services.project_service import project_service
from app.models.project import Project, ProjectStatus


STATUS_COLORS = {
    ProjectStatus.IMPORTING: MUTED,
    ProjectStatus.READY: SUCCESS,
    ProjectStatus.QUEUED: WARNING,
    ProjectStatus.PROCESSING: WARNING,
    ProjectStatus.COMPLETED: SUCCESS,
    ProjectStatus.FAILED: ERROR,
}

# =====================================================
# PROJECT ROW
# =====================================================


class ProjectRow(QFrame):

    def __init__(self, name, modified, model, resolution, status, color):
        super().__init__()

        self.setObjectName("ProjectRow")
        self.setFixedHeight(120)

        self.setStyleSheet(f"""
        QFrame#ProjectRow{{
            background:{CARD};
            border:1px solid {BORDER};
            border-radius:18px;
        }}

        QFrame#ProjectRow:hover{{
            background:{CARD_HOVER};
            border:1px solid {ACCENT};
        }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(18)

        # ====================================
        # Thumbnail
        # ====================================

        thumb = QLabel("▶")
        thumb.setObjectName("Thumbnail")
        thumb.setFixedSize(140, 84)
        thumb.setAlignment(Qt.AlignCenter)

        thumb.setStyleSheet(f"""
        QLabel#Thumbnail{{
            background:qlineargradient(
                x1:0,y1:0,
                x2:1,y2:1,
                stop:0 #355C9C,
                stop:1 #1B273D
            );
            border-radius:12px;
            color:{TEXT};
            font-size:30px;
            background:transparent;
            border:none;
        }}
        """)

        layout.addWidget(thumb)

        # ====================================
        # Information
        # ====================================

        info = QVBoxLayout()
        info.setSpacing(5)

        title = QLabel(name)
        title.setStyleSheet(f"""
            color:{TEXT};
            font-size:18px;
            font-weight:700;
            background:transparent;
            border:none;
        """)

        modifiedLabel = QLabel(modified)
        modifiedLabel.setStyleSheet(f"""
            color:{SECONDARY};
            font-size:13px;
            background:transparent;
            border:none;
        """)

        details = QLabel(f"{model} • {resolution}")
        details.setStyleSheet(f"""
            color:{MUTED};
            font-size:12px;
            background:transparent;
            border:none;
        """)

        info.addWidget(title)
        info.addWidget(modifiedLabel)
        info.addWidget(details)

        layout.addLayout(info)

        layout.addStretch()

        # ====================================
        # Right Side
        # ====================================

        right = QVBoxLayout()

        statusLabel = QLabel(f"● {status}")
        statusLabel.setAlignment(Qt.AlignRight)

        statusLabel.setStyleSheet(f"""
            color:{color};
            font-size:13px;
            font-weight:600;
            background:transparent;
            border:none;
        """)

        menu = QPushButton("⋮")
        menu.setCursor(Qt.PointingHandCursor)
        menu.setFixedSize(34, 34)

        menu.setStyleSheet(f"""
        QPushButton{{
            background:transparent;
            border:none;
            color:{MUTED};
            font-size:20px;
        }}

        QPushButton:hover{{
            color:{TEXT};
        }}
        """)

        right.addWidget(statusLabel)
        right.addStretch()
        right.addWidget(menu, alignment=Qt.AlignRight)

        layout.addLayout(right)


# =====================================================
# RECENT PROJECTS
# =====================================================


class RecentProjects(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # ====================================
        # Header
        # ====================================

        header = QHBoxLayout()

        title = QLabel("Recent Projects")
        title.setStyleSheet(f"""
            color:{TEXT};
            font-size:24px;
            font-weight:700;
            background:transparent;
            border:none;
        """)

        viewAll = QPushButton("View All")
        viewAll.setCursor(Qt.PointingHandCursor)

        viewAll.setStyleSheet(f"""
        QPushButton{{
            background:transparent;
            border:none;
            color:{ACCENT};
            font-size:14px;
            font-weight:600;
        }}

        QPushButton:hover{{
            color:{TEXT};
        }}
        """)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(viewAll)

        layout.addLayout(header)

        # ====================================
        # Project List
        # ====================================

        self.list_layout = QVBoxLayout()
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(16)
        layout.addLayout(self.list_layout)

        self.refresh()

    def refresh(self):
        """Rebuild project rows from the current project service list."""
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for project in project_service.get_projects():
            self.list_layout.addWidget(row_for_project(project))


def imported_label(imported_at: datetime) -> str:
    elapsed = datetime.now() - imported_at
    seconds = max(0, int(elapsed.total_seconds()))
    if seconds < 60:
        return "Imported just now"
    if seconds < 3600:
        minutes = seconds // 60
        unit = "minute" if minutes == 1 else "minutes"
        return f"Imported {minutes} {unit} ago"
    if seconds < 86400:
        hours = seconds // 3600
        unit = "hour" if hours == 1 else "hours"
        return f"Imported {hours} {unit} ago"
    days = seconds // 86400
    if days == 1:
        return "Imported yesterday"
    return f"Imported {days} days ago"


def row_for_project(project: Project) -> ProjectRow:
    return ProjectRow(
        project.filename,
        imported_label(project.created_at),
        project.ai_model,
        project.display_resolution,
        project.status.value,
        STATUS_COLORS.get(project.status, MUTED),
    )
