from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QFrame,
)

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from app.theme import *
from app.sidebar_button import SidebarButton


class Sidebar(QWidget):

    section_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._current_section = "Dashboard"

        # =====================================
        # Sidebar Size
        # =====================================

        self.setFixedWidth(255)

        # =====================================
        # Sidebar Style
        # =====================================

        self.setStyleSheet(f"""
        QWidget {{
            background-color: {SIDEBAR};
            border-right: 1px solid rgba(59,130,246,120);
        }}
        """)

        # =====================================
        # Main Layout
        # =====================================

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 24, 22, 20)
        layout.setSpacing(0)

        # =====================================
        # Logo
        # =====================================

        logo = QWidget()

        logo_layout = QVBoxLayout(logo)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(2)

        title = QLabel("VIDEL")
        title.setAlignment(Qt.AlignLeft)

        title.setStyleSheet(f"""
            color: {SECONDARY};
            font-size: 34px;
            font-weight: 800;
            letter-spacing: 1px;
            background:transparent;
            border:none;
        """)

        subtitle = QLabel("Video Eloquence")

        subtitle.setStyleSheet(f"""
            color: {SECONDARY};
            font-size: 12px;
            background:transparent;
            border:none;
        """)

        logo_layout.addWidget(title)
        logo_layout.addWidget(subtitle)

        layout.addWidget(logo)

        layout.addSpacing(35)

        # =====================================
        # Navigation
        # =====================================

        buttons = [
            ("assets/icons/dashboard.svg", "Dashboard"),
            ("assets/icons/projects.svg", "Projects"),
            ("assets/icons/enhance.svg", "AI Enhance"),
            ("assets/icons/export.svg", "Export"),
            ("assets/icons/settings.svg", "Settings"),
        ]

        self.buttons = []

        for icon_path, text in buttons:

            button = SidebarButton(text)

            button.setIcon(QIcon(icon_path))

            if text == "Dashboard":
                button.setChecked(True)

            button.clicked.connect(lambda checked=False, section=text: self._on_section(section))

            layout.addWidget(button)
            layout.addSpacing(12)

            self.buttons.append(button)

        layout.addStretch()

        # =====================================
        # Divider
        # =====================================

        divider = QFrame()
        divider.setFixedHeight(1)

        divider.setStyleSheet("""
            background: rgba(59,130,246,80);
            border: none;
        """)

        layout.addWidget(divider)

        layout.addSpacing(12)

        # =====================================
        # Version
        # =====================================

        version = QLabel("Videl v0.1.0")

        version.setStyleSheet(f"""
            color: {MUTED};
            font-size: 11px;
            background:transparent;
            border:none;
        """)

        layout.addWidget(version)

    def _on_section(self, text):
        if text not in ("Dashboard", "Projects", "AI Enhance"):
            for button in self.buttons:
                button.setChecked(button.text() == self._current_section)
            return

        self._current_section = text
        for button in self.buttons:
            button.setChecked(button.text() == text)
        self.section_changed.emit(text)
