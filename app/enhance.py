from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QScrollArea,
    QComboBox,
    QPushButton,
    QProgressBar,
)

from PySide6.QtCore import Qt, Signal
from app.theme import *
from app.services.project_service import project_service
from app.services.ffmpeg_tools import ffmpeg_status_text, ffprobe_status_text, probe_video
from app.services.video_processor import VideoProcessor
from app.models.project import ProjectStatus

STATUS_COLORS = {
    ProjectStatus.IMPORTING: MUTED,
    ProjectStatus.READY: SUCCESS,
    ProjectStatus.QUEUED: WARNING,
    ProjectStatus.PROCESSING: WARNING,
    ProjectStatus.COMPLETED: SUCCESS,
    ProjectStatus.FAILED: ERROR,
}


ENHANCEMENT_MODELS = [
    "VIDEL Neural v4",
    "Natural Restore",
    "HDR AI",
]

OUTPUT_RESOLUTIONS = [
    "Original",
    "1080p",
    "1440p",
    "4K UHD",
    "8K",
]

ENHANCEMENT_MODES = [
    "Standard",
    "High Quality",
    "Maximum Quality",
]


class EnhancePage(QWidget):

    projects_changed = Signal()

    def __init__(self):
        super().__init__()

        self._loading = False
        self.setObjectName("EnhancePage")

        self.setStyleSheet(f"""
        QWidget#EnhancePage {{
            background: {BACKGROUND};
        }}

        QComboBox {{
            background:{CARD};
            color:{TEXT};
            border:1px solid {BORDER};
            border-radius:14px;
            padding:10px 14px;
            font-size:14px;
            min-height:24px;
        }}

        QComboBox:hover {{
            border:1px solid {ACCENT};
        }}

        QComboBox::drop-down {{
            border:none;
            width:28px;
        }}

        QComboBox QAbstractItemView {{
            background:{CARD};
            color:{TEXT};
            border:1px solid {BORDER};
            selection-background-color:{ACCENT_DARK};
            selection-color:{TEXT};
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
        container.setStyleSheet(f"background:{BACKGROUND};")

        content = QVBoxLayout(container)
        content.setContentsMargins(55, 35, 55, 35)
        content.setSpacing(20)

        title = QLabel("AI Enhance")
        title.setStyleSheet(f"""
            color:{TEXT};
            font-size:24px;
            font-weight:700;
            background:transparent;
            border:none;
        """)
        content.addWidget(title)

        self.tools_label = QLabel(f"{ffmpeg_status_text()}  •  {ffprobe_status_text()}")
        self.tools_label.setStyleSheet(f"""
            color:{MUTED};
            font-size:12px;
            background:transparent;
            border:none;
        """)
        content.addWidget(self.tools_label)

        self.empty_label = QLabel("Please import a video first.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet(f"""
            color:{SECONDARY};
            font-size:16px;
            background:{CARD};
            border:1px solid {BORDER};
            border-radius:18px;
            padding:36px;
        """)
        content.addWidget(self.empty_label)

        self.workspace = QWidget()
        self.workspace.setStyleSheet("background:transparent; border:none;")
        workspace_layout = QVBoxLayout(self.workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(20)

        info = QFrame()
        info.setObjectName("EnhanceInfo")
        info.setStyleSheet(f"""
        QFrame#EnhanceInfo {{
            background:{CARD};
            border:1px solid {BORDER};
            border-radius:18px;
        }}
        """)
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(22, 20, 22, 20)
        info_layout.setSpacing(8)

        self.filename_label = QLabel()
        self.filename_label.setStyleSheet(f"""
            color:{TEXT};
            font-size:22px;
            font-weight:700;
            background:transparent;
            border:none;
        """)

        self.status_label = QLabel()
        self.resolution_label = QLabel()
        self.resolution_label.setStyleSheet(f"""
            color:{MUTED};
            font-size:13px;
            background:transparent;
            border:none;
        """)

        self.metadata_label = QLabel()
        self.metadata_label.setWordWrap(True)
        self.metadata_label.setStyleSheet(f"""
            color:{MUTED};
            font-size:12px;
            background:transparent;
            border:none;
        """)

        info_layout.addWidget(self.filename_label)
        info_layout.addWidget(self.status_label)
        info_layout.addWidget(self.resolution_label)
        info_layout.addWidget(self.metadata_label)
        workspace_layout.addWidget(info)

        preview = QFrame()
        preview.setObjectName("EnhancePreview")
        preview.setFixedHeight(240)
        preview.setStyleSheet(f"""
        QFrame#EnhancePreview {{
            background:qlineargradient(
                x1:0,y1:0,
                x2:1,y2:1,
                stop:0 #355C9C,
                stop:1 #1B273D
            );
            border:1px solid {BORDER};
            border-radius:18px;
        }}
        """)
        preview_layout = QVBoxLayout(preview)
        preview_icon = QLabel("▶")
        preview_icon.setAlignment(Qt.AlignCenter)
        preview_icon.setStyleSheet(f"""
            color:{TEXT};
            font-size:48px;
            background:transparent;
            border:none;
        """)
        preview_caption = QLabel("Preview")
        preview_caption.setAlignment(Qt.AlignCenter)
        preview_caption.setStyleSheet(f"""
            color:{SECONDARY};
            font-size:13px;
            background:transparent;
            border:none;
        """)
        preview_layout.addStretch()
        preview_layout.addWidget(preview_icon)
        preview_layout.addWidget(preview_caption)
        preview_layout.addStretch()
        workspace_layout.addWidget(preview)

        settings = QFrame()
        settings.setObjectName("EnhanceSettings")
        settings.setStyleSheet(f"""
        QFrame#EnhanceSettings {{
            background:{CARD};
            border:1px solid {BORDER};
            border-radius:18px;
        }}
        """)
        settings_layout = QVBoxLayout(settings)
        settings_layout.setContentsMargins(22, 20, 22, 20)
        settings_layout.setSpacing(14)

        settings_title = QLabel("Enhancement settings")
        settings_title.setStyleSheet(f"""
            color:{TEXT};
            font-size:18px;
            font-weight:700;
            background:transparent;
            border:none;
        """)
        settings_layout.addWidget(settings_title)

        self.model_combo = self._make_combo(ENHANCEMENT_MODELS)
        self.resolution_combo = self._make_combo(OUTPUT_RESOLUTIONS)
        self.mode_combo = self._make_combo(ENHANCEMENT_MODES)

        settings_layout.addLayout(self._labeled_row("Model", self.model_combo))
        settings_layout.addLayout(self._labeled_row("Output resolution", self.resolution_combo))
        settings_layout.addLayout(self._labeled_row("Enhancement mode", self.mode_combo))
        workspace_layout.addWidget(settings)

        self.start_button = QPushButton("Start Enhancement")
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.setFixedHeight(52)
        self.start_button.setStyleSheet(f"""
        QPushButton {{
            background:{ACCENT};
            color:{TEXT};
            border:none;
            border-radius:16px;
            font-size:16px;
            font-weight:700;
            padding:14px 32px;
        }}
        QPushButton:hover {{
            background:{ACCENT_HOVER};
        }}
        QPushButton:pressed {{
            background:{ACCENT_DARK};
        }}
        """)
        self.start_button.clicked.connect(self.start_enhancement)
        workspace_layout.addWidget(self.start_button, alignment=Qt.AlignLeft)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
        QProgressBar {{
            background:{PANEL};
            border:1px solid {BORDER};
            border-radius:6px;
        }}
        QProgressBar::chunk {{
            background:{ACCENT};
            border-radius:6px;
        }}
        """)
        workspace_layout.addWidget(self.progress_bar)

        self.message_label = QLabel()
        self.message_label.setStyleSheet(f"""
            color:{ACCENT};
            font-size:14px;
            font-weight:600;
            background:transparent;
            border:none;
        """)
        workspace_layout.addWidget(self.message_label)

        content.addWidget(self.workspace)
        content.addStretch()

        scroll.setWidget(container)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        self.model_combo.currentTextChanged.connect(self._save_settings)
        self.resolution_combo.currentTextChanged.connect(self._save_settings)
        self.mode_combo.currentTextChanged.connect(self._save_settings)

        self.processor = VideoProcessor(self)
        self.processor.job_queued.connect(self._on_job_queued)
        self.processor.job_started.connect(self._on_job_started)
        self.processor.job_progress.connect(self._on_job_progress)
        self.processor.job_completed.connect(self._on_job_completed)
        self.processor.job_failed.connect(self._on_job_failed)

        self.load_current_project()

    def _make_combo(self, items):
        combo = QComboBox()
        combo.addItems(items)
        combo.setCursor(Qt.PointingHandCursor)
        combo.setMinimumWidth(280)
        return combo

    def _labeled_row(self, title, combo):
        row = QVBoxLayout()
        row.setSpacing(6)
        label = QLabel(title)
        label.setStyleSheet(f"""
            color:{MUTED};
            font-size:12px;
            font-weight:600;
            background:transparent;
            border:none;
        """)
        row.addWidget(label)
        row.addWidget(combo)
        return row

    def showEvent(self, event):
        self.load_current_project()
        super().showEvent(event)

    def load_current_project(self):
        project = project_service.current_project
        if project is None:
            self.workspace.hide()
            self.empty_label.show()
            return

        self.empty_label.hide()
        self.workspace.show()

        # Probe video if metadata is missing
        if project.metadata is None or project.metadata.width is None:
            try:
                metadata = probe_video(project.file_path)
                project.metadata = metadata
            except Exception as e:
                print(f"Failed to probe video: {e}")

        self.filename_label.setText(project.filename)
        color = STATUS_COLORS.get(project.status, MUTED)
        self.status_label.setText(f"● {project.status.value}")
        self.status_label.setStyleSheet(f"""
            color:{color};
            font-size:13px;
            font-weight:600;
            background:transparent;
            border:none;
        """)
        self.resolution_label.setText(f"Current resolution: {project.display_resolution}")
        self.metadata_label.setText(self._metadata_summary(project))

        self._loading = True
        self._set_combo(self.model_combo, project.ai_model)
        self._set_combo(self.resolution_combo, project.output_resolution)
        self._set_combo(self.mode_combo, project.enhancement_mode)
        self._loading = False

        busy = project.status in (ProjectStatus.QUEUED, ProjectStatus.PROCESSING)
        self.start_button.setEnabled(not busy)
        self._update_progress_bar(project)
        self._update_message(project)

    def _metadata_summary(self, project) -> str:
        meta = project.metadata
        if meta is None:
            return "Duration: Unknown  •  Container: Unknown  •  Video: Unknown  •  Audio: Unknown  •  FPS: Unknown  •  Size: Unknown"
        return (
            f"Duration: {project.duration_string}"
            f"  •  Container: {meta.container_display}"
            f"  •  Video: {meta.video_codec_display}"
            f"  •  Audio: {meta.audio_codec_display}"
            f"  •  FPS: {meta.frame_rate_display}"
            f"  •  Size: {project.file_size_string}"
        )

    def _update_message(self, project):
        if project.status == ProjectStatus.QUEUED:
            self.message_label.setText("Enhancement queued")
            self.message_label.setStyleSheet(self._message_style(ACCENT))
        elif project.status == ProjectStatus.PROCESSING:
            self.message_label.setText("Enhancing video...")
            self.message_label.setStyleSheet(self._message_style(ACCENT))
        elif project.status == ProjectStatus.COMPLETED:
            self.message_label.setText("Enhancement complete")
            self.message_label.setStyleSheet(self._message_style(SUCCESS))
        elif project.status == ProjectStatus.FAILED:
            error_msg = project.error_message or "Enhancement failed"
            self.message_label.setText(f"Enhancement failed: {error_msg}")
            self.message_label.setStyleSheet(self._message_style(ERROR))
        else:
            self.message_label.clear()

    def _message_style(self, color):
        return f"""
            color:{color};
            font-size:14px;
            font-weight:600;
            background:transparent;
            border:none;
        """

    def _update_progress_bar(self, project):
        if project.status not in (ProjectStatus.QUEUED, ProjectStatus.PROCESSING, ProjectStatus.COMPLETED):
            self.progress_bar.setVisible(False)
            return
        self.progress_bar.setVisible(True)
        if project.status == ProjectStatus.PROCESSING and project.progress is None:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)
            value = 100 if project.status == ProjectStatus.COMPLETED else (project.progress or 0)
            self.progress_bar.setValue(value)

    def _set_combo(self, combo, value):
        index = combo.findText(value)
        combo.setCurrentIndex(index if index >= 0 else 0)

    def _save_settings(self):
        if self._loading:
            return
        project = project_service.current_project
        if project is None:
            return
        project.ai_model = self.model_combo.currentText()
        project.output_resolution = self.resolution_combo.currentText()
        project.enhancement_mode = self.mode_combo.currentText()

    def start_enhancement(self):
        project = project_service.current_project
        if project is None:
            self.workspace.hide()
            self.empty_label.show()
            self.empty_label.setText("Please import a video first.")
            return

        self._save_settings()
        if self.processor.is_busy():
            self.message_label.setText("A processing job is already running.")
            self.message_label.setStyleSheet(self._message_style(WARNING))
            return

        job = self.processor.start_job(project)
        if job is None:
            self.message_label.setText(project.error_message or "Could not start processing.")
            self.message_label.setStyleSheet(self._message_style(ERROR))
            return

    def _on_job_queued(self, job):
        self.load_current_project()
        self.projects_changed.emit()

    def _on_job_started(self, job):
        self.load_current_project()
        self.projects_changed.emit()

    def _on_job_progress(self, job, percent):
        project = project_service.current_project
        if project is None:
            return
        if percent is None:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(int(percent))

    def _on_job_completed(self, job):
        self.load_current_project()
        self.projects_changed.emit()

    def _on_job_failed(self, job, message):
        self.load_current_project()
        self.projects_changed.emit()
