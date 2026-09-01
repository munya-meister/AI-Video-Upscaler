from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class ProjectStatus(Enum):
    IMPORTING = "IMPORTING"
    READY = "READY"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


def display_or_unknown(value) -> str:
    if value is None or value == "":
        return "Unknown"
    return str(value)


@dataclass
class VideoMetadata:
    """Metadata extracted from video files"""
    duration: Optional[float] = None  # in seconds
    width: Optional[int] = None
    height: Optional[int] = None
    resolution: Optional[str] = None
    file_size: Optional[int] = None  # in bytes
    codec: Optional[str] = None
    container: Optional[str] = None
    frame_rate: Optional[float] = None
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None

    @property
    def container_display(self) -> str:
        return display_or_unknown(self.container)

    @property
    def video_codec_display(self) -> str:
        return display_or_unknown(self.video_codec or self.codec)

    @property
    def audio_codec_display(self) -> str:
        return display_or_unknown(self.audio_codec)

    @property
    def frame_rate_display(self) -> str:
        if self.frame_rate:
            return f"{self.frame_rate:.2f} fps"
        return "Unknown"


@dataclass
class ProcessingJob:
    """A video processing job using FFmpeg-based enhancement."""
    project_id: str
    input_path: str
    output_path: str
    model: str
    resolution: str
    enhancement_mode: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: ProjectStatus = ProjectStatus.QUEUED
    progress: Optional[int] = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class Project:
    """Represents a video enhancement project"""
    filename: str
    file_path: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    status: ProjectStatus = ProjectStatus.IMPORTING
    metadata: Optional[VideoMetadata] = None
    ai_model: str = "VIDEL Neural v4"
    output_resolution: str = "Original"
    enhancement_mode: str = "Standard"
    output_path: Optional[str] = None
    progress: Optional[int] = None
    error_message: Optional[str] = None
    
    @property
    def resolution(self) -> str:
        """Get resolution string from metadata"""
        if self.metadata and self.metadata.width and self.metadata.height:
            return f"{self.metadata.width}x{self.metadata.height}"
        return "Unknown"
    
    @property
    def display_resolution(self) -> str:
        """Get human-readable resolution"""
        if self.metadata and self.metadata.width and self.metadata.height:
            # Convert to common resolution names
            width, height = self.metadata.width, self.metadata.height
            if width >= 7680:
                return "8K"
            elif width >= 3840:
                return "4K"
            elif width >= 2560:
                return "2K"
            elif width >= 1920:
                return "1080p"
            elif width >= 1280:
                return "720p"
            else:
                return f"{width}x{height}"
        return "Unknown"
    
    @property
    def duration_string(self) -> str:
        """Get human-readable duration"""
        if self.metadata and self.metadata.duration:
            minutes = int(self.metadata.duration // 60)
            seconds = int(self.metadata.duration % 60)
            return f"{minutes}:{seconds:02d}"
        return "Unknown"
    
    @property
    def file_size_string(self) -> str:
        """Get human-readable file size"""
        if self.metadata and self.metadata.file_size:
            size = self.metadata.file_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        return "Unknown"
    
    def update_status(self, status: ProjectStatus):
        """Update project status and modified time"""
        self.status = status
        self.modified_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert project to dictionary for serialization"""
        return {
            'id': self.id,
            'filename': self.filename,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'status': self.status.value,
            'metadata': {
                'duration': self.metadata.duration if self.metadata else None,
                'width': self.metadata.width if self.metadata else None,
                'height': self.metadata.height if self.metadata else None,
                'resolution': self.metadata.resolution if self.metadata else None,
                'file_size': self.metadata.file_size if self.metadata else None,
                'codec': self.metadata.codec if self.metadata else None,
                'container': self.metadata.container if self.metadata else None,
                'frame_rate': self.metadata.frame_rate if self.metadata else None,
                'video_codec': self.metadata.video_codec if self.metadata else None,
                'audio_codec': self.metadata.audio_codec if self.metadata else None,
            } if self.metadata else None,
            'ai_model': self.ai_model,
            'output_resolution': self.output_resolution,
            'enhancement_mode': self.enhancement_mode,
            'output_path': self.output_path,
            'progress': self.progress,
            'error_message': self.error_message,
        }
