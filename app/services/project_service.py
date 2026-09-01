from typing import List, Optional
from datetime import datetime
from pathlib import Path
from app.models.project import Project, ProjectStatus, VideoMetadata
from app.services.ffmpeg_tools import probe_video


class ProjectService:
    """Service for managing video enhancement projects"""
    
    def __init__(self):
        self.projects: List[Project] = []
        self.current_project: Optional[Project] = None
        self._load_sample_projects()
    
    def _load_sample_projects(self):
        """Load sample projects for demonstration"""
        # These will be replaced with real projects as users import videos
        sample_projects = [
            Project(
                filename="Wedding_Edit.mp4",
                file_path="/path/to/Wedding_Edit.mp4",
                created_at=datetime.now(),
                modified_at=datetime.now(),
                status=ProjectStatus.COMPLETED,
                metadata=VideoMetadata(
                    duration=180.5,  # 3 minutes
                    width=3840,
                    height=2160,
                    resolution="4K",
                    file_size=1500000000,  # ~1.5GB
                ),
                ai_model="VIDEL Neural v4"
            ),
            Project(
                filename="Podcast_Episode.mov",
                file_path="/path/to/Podcast_Episode.mov",
                created_at=datetime.now(),
                modified_at=datetime.now(),
                status=ProjectStatus.PROCESSING,
                metadata=VideoMetadata(
                    duration=2400.0,  # 40 minutes
                    width=1920,
                    height=1080,
                    resolution="1080p",
                    file_size=800000000,  # ~800MB
                ),
                ai_model="Natural Restore"
            ),
            Project(
                filename="Music_Video.mp4",
                file_path="/path/to/Music_Video.mp4",
                created_at=datetime.now(),
                modified_at=datetime.now(),
                status=ProjectStatus.COMPLETED,
                metadata=VideoMetadata(
                    duration=210.0,  # 3.5 minutes
                    width=7680,
                    height=4320,
                    resolution="8K",
                    file_size=2500000000,  # ~2.5GB
                ),
                ai_model="HDR AI"
            ),
        ]
        self.projects = sample_projects
    
    def create_project(self, file_path: str, metadata: Optional[VideoMetadata] = None) -> Project:
        """Create a new project from a video file"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        project = Project(
            filename=path.name,
            file_path=str(path.absolute()),
            created_at=datetime.now(),
            modified_at=datetime.now(),
            status=ProjectStatus.READY,
            metadata=metadata,
        )
        
        self.projects.insert(0, project)  # Add to beginning of list
        return project

    def get_project_by_path(self, file_path: str) -> Optional[Project]:
        """Find an existing project by normalized file path."""
        try:
            target = str(Path(file_path).resolve()).lower()
        except OSError:
            target = str(Path(file_path)).lower()

        for project in self.projects:
            try:
                current = str(Path(project.file_path).resolve()).lower()
            except OSError:
                current = str(project.file_path).lower()
            if current == target:
                return project
        return None

    def extract_metadata(self, file_path: str) -> Optional[VideoMetadata]:
        """Best-effort metadata extraction. Never crashes the import."""
        try:
            return probe_video(file_path)
        except Exception:
            return None

    def import_video(self, file_path: str) -> Project:
        """Create or update a project for a selected video. Newest first, no duplicates."""
        path = Path(file_path)
        try:
            resolved = str(path.resolve())
        except OSError:
            resolved = str(path)

        metadata = self.extract_metadata(resolved)
        existing = self.get_project_by_path(resolved)

        if existing:
            existing.filename = path.name
            existing.file_path = resolved
            existing.update_status(ProjectStatus.READY)
            if metadata is not None:
                existing.metadata = metadata
            self.projects.remove(existing)
            self.projects.insert(0, existing)
            self.current_project = existing
            return existing

        try:
            project = self.create_project(resolved, metadata)
        except FileNotFoundError:
            project = Project(
                filename=path.name,
                file_path=resolved,
                created_at=datetime.now(),
                modified_at=datetime.now(),
                status=ProjectStatus.READY,
                metadata=metadata,
            )
            self.projects.insert(0, project)

        self.current_project = project
        return project
    
    def get_projects(self) -> List[Project]:
        """Get all projects, sorted by modification date (newest first)"""
        return sorted(self.projects, key=lambda p: p.modified_at, reverse=True)
    
    def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """Get a project by its unique id."""
        for project in self.projects:
            if project.id == project_id:
                return project
        return None
    
    def update_project_status(self, project: Project, status: ProjectStatus):
        """Update the status of a project"""
        project.update_status(status)

    def queue_enhancement(self, project: Project) -> Project:
        """Mark a project as queued without starting real processing."""
        self.update_project_status(project, ProjectStatus.QUEUED)
        self.current_project = project
        return project
    
    def search_projects(self, query: str) -> List[Project]:
        """Search projects by filename, status, or AI model"""
        query = query.lower()
        results = []
        
        for project in self.projects:
            if (query in project.filename.lower() or 
                query in project.status.value.lower() or
                query in project.ai_model.lower()):
                results.append(project)
        
        return results
    
    def delete_project(self, project: Project):
        """Delete a project from the list"""
        if project in self.projects:
            self.projects.remove(project)


# Global project service instance
project_service = ProjectService()