from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QFileDialog,
)

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from app.theme import *


class UploadCard(QFrame):
    file_selected = Signal(str)  # Signal emitted when a file is selected

    def __init__(self):
        super().__init__()

        self.setFixedHeight(420)

        self.setObjectName("uploadCard")

        self.setAcceptDrops(True)

        self.setStyleSheet(f"""
        QFrame#uploadCard{{
            background:qlineargradient(
                x1:0,y1:0,
                x2:1,y2:1,
                stop:0 {ACCENT_DARK},
                stop:1 {ACCENT_HOVER}
            );
            border:1px solid {ACCENT};
            border-radius:28px;
        }}

        QLabel#title{{
            color:{TEXT};
            font-size:36px;
            font-weight:700;
            background:transparent;
            border:none;
        }}

        QLabel#subtitle{{
            color:{SECONDARY};
            font-size:16px;
            background:transparent;
            border:none;
        }}

        QLabel#support{{
            color:rgba(255,255,255,180);
            font-size:14px;
            background:transparent;
            border:none;
        }}

        QPushButton{{
            background:white;
            color:{ACCENT_DARK};
            border:none;
            border-radius:16px;
            font-size:16px;
            font-weight:700;
            padding:14px 32px;
        }}

        QPushButton:hover{{
            background:rgba(255,255,255,0.9);
        }}

        QPushButton:pressed{{
            background:rgba(255,255,255,0.8);
        }}
        """)

        layout = QVBoxLayout(self)

        layout.setAlignment(Qt.AlignCenter)

        layout.setSpacing(12)

        layout.setContentsMargins(60, 50, 60, 50)

        # ============================
        # Upload Icon
        # ============================

        badge = QLabel("↑")

        badge.setAlignment(Qt.AlignCenter)

        badge.setFixedSize(100, 100)

        badge.setStyleSheet("""
        QLabel{
            background:rgba(255,255,255,0.15);
            border-radius:50px;
            color:white;
            font-size:48px;
            font-weight:bold;
        }
        """)

        # ============================

        self.title = QLabel("Upload Video")
        self.title.setObjectName("title")
        self.title.setAlignment(Qt.AlignCenter)

        self.subtitle = QLabel("Drag & Drop your video\nor browse your computer")

        self.subtitle.setObjectName("subtitle")
        self.subtitle.setAlignment(Qt.AlignCenter)

        self.support = QLabel("MP4 • MOV • AVI • MKV • WEBM\nUp to 8K Resolution")

        self.support.setObjectName("support")
        self.support.setAlignment(Qt.AlignCenter)

        self.browse = QPushButton("Browse Files")
        self.browse.setCursor(Qt.PointingHandCursor)
        self.browse.setFixedWidth(220)
        self.browse.setFixedHeight(50)
        self.browse.clicked.connect(self.browse_files)

        self.browse_another = QPushButton("Browse Another Video")
        self.browse_another.setCursor(Qt.PointingHandCursor)
        self.browse_another.setFixedHeight(50)
        self.browse_another.clicked.connect(self.browse_files)
        self.browse_another.hide()

        button_row = QHBoxLayout()
        button_row.setAlignment(Qt.AlignCenter)
        button_row.setSpacing(12)
        button_row.addWidget(self.browse)
        button_row.addWidget(self.browse_another)

        # ============================

        layout.addStretch()

        layout.addWidget(badge, alignment=Qt.AlignCenter)

        layout.addSpacing(20)

        layout.addWidget(self.title)

        layout.addSpacing(8)

        layout.addWidget(self.subtitle)

        layout.addSpacing(16)

        layout.addWidget(self.support)

        layout.addSpacing(28)

        layout.addLayout(button_row)

        layout.addStretch()

    def update_upload_display(self, file_path):
        """Update the upload card to show the selected file"""
        from pathlib import Path
        filename = Path(file_path).name
        
        # Update the title to show the selected filename
        self.title.setText(filename)
        self.subtitle.setText("File selected successfully")
        self.support.setText("Ready for enhancement")
        
        # Change the button to "Change File"
        self.browse.setText("Change File")
        self.browse_another.show()

    def show_error_message(self, message):
        """Show an error message temporarily"""
        original_title = self.title.text()
        original_subtitle = self.subtitle.text()
        
        self.title.setText("Error")
        self.subtitle.setText(message)
        self.support.setText("Please try again")
        
        # Reset after 2 seconds (would use QTimer in production)
        # For now, manual reset would be needed

    def browse_files(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Video Files (*.mp4 *.mov *.avi *.mkv *.webm)")
        file_dialog.setViewMode(QFileDialog.Detail)
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                self.file_selected.emit(file_path)
                self.update_upload_display(file_path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            # Check if any of the URLs is a valid video file
            urls = event.mimeData().urls()
            valid_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
            from pathlib import Path
            
            has_valid_file = any(Path(url.toLocalFile()).suffix.lower() in valid_extensions for url in urls)
            
            if has_valid_file:
                event.acceptProposedAction()
                self.setStyleSheet(f"""
                QFrame#uploadCard{{
                    background:qlineargradient(
                        x1:0,y1:0,
                        x2:1,y2:1,
                        stop:0 {ACCENT},
                        stop:1 {ACCENT_HOVER}
                    );
                    border:2px solid white;
                    border-radius:28px;
                }}
                QLabel#title{{
                    color:{TEXT};
                    font-size:36px;
                    font-weight:700;
                    background:transparent;
                    border:none;
                }}
                QLabel#subtitle{{
                    color:{SECONDARY};
                    font-size:16px;
                    background:transparent;
                    border:none;
                }}
                QLabel#support{{
                    color:rgba(255,255,255,180);
                    font-size:14px;
                    background:transparent;
                    border:none;
                }}
                QPushButton{{
                    background:white;
                    color:{ACCENT_DARK};
                    border:none;
                    border-radius:16px;
                    font-size:16px;
                    font-weight:700;
                    padding:14px 32px;
                }}
                QPushButton:hover{{
                    background:rgba(255,255,255,0.9);
                }}
                QPushButton:pressed{{
                    background:rgba(255,255,255,0.8);
                }}
                """)
            else:
                event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(f"""
        QFrame#uploadCard{{
            background:qlineargradient(
                x1:0,y1:0,
                x2:1,y2:1,
                stop:0 {ACCENT_DARK},
                stop:1 {ACCENT_HOVER}
            );
            border:1px solid {ACCENT};
            border-radius:28px;
        }}
        QLabel#title{{
            color:{TEXT};
            font-size:36px;
            font-weight:700;
            background:transparent;
            border:none;
        }}
        QLabel#subtitle{{
            color:{SECONDARY};
            font-size:16px;
            background:transparent;
            border:none;
        }}
        QLabel#support{{
            color:rgba(255,255,255,180);
            font-size:14px;
            background:transparent;
            border:none;
        }}
        QPushButton{{
            background:white;
            color:{ACCENT_DARK};
            border:none;
            border-radius:16px;
            font-size:16px;
            font-weight:700;
            padding:14px 32px;
        }}
        QPushButton:hover{{
            background:rgba(255,255,255,0.9);
        }}
        QPushButton:pressed{{
            background:rgba(255,255,255,0.8);
        }}
        """)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                # Check if it's a valid video file
                valid_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
                from pathlib import Path
                if Path(file_path).suffix.lower() in valid_extensions:
                    self.file_selected.emit(file_path)
                    self.update_upload_display(file_path)
                    event.acceptProposedAction()
                else:
                    # Reject unsupported files
                    event.ignore()
                    return
        
        # Reset styling
        self.setStyleSheet(f"""
        QFrame#uploadCard{{
            background:qlineargradient(
                x1:0,y1:0,
                x2:1,y2:1,
                stop:0 {ACCENT_DARK},
                stop:1 {ACCENT_HOVER}
            );
            border:1px solid {ACCENT};
            border-radius:28px;
        }}
        QLabel#title{{
            color:{TEXT};
            font-size:36px;
            font-weight:700;
            background:transparent;
            border:none;
        }}
        QLabel#subtitle{{
            color:{SECONDARY};
            font-size:16px;
            background:transparent;
            border:none;
        }}
        QLabel#support{{
            color:rgba(255,255,255,180);
            font-size:14px;
            background:transparent;
            border:none;
        }}
        QPushButton{{
            background:white;
            color:{ACCENT_DARK};
            border:none;
            border-radius:16px;
            font-size:16px;
            font-weight:700;
            padding:14px 32px;
        }}
        QPushButton:hover{{
            background:rgba(255,255,255,0.9);
        }}
        QPushButton:pressed{{
            background:rgba(255,255,255,0.8);
        }}
        """)
