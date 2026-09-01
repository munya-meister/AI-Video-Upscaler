import os
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QThread, Signal

from app.models.project import ProcessingJob, Project, ProjectStatus
from app.services.ffmpeg_tools import (
    ffmpeg_available,
    ffmpeg_path,
    output_is_valid,
    ffprobe_path,
    probe_video,
)
from app.services.project_service import project_service


APP_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = APP_ROOT / "output"


def build_output_path(input_path: str) -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source = Path(input_path)
    stem = source.stem or "video"
    suffix = source.suffix or ".mp4"
    candidate = OUTPUT_DIR / f"{stem}_enhanced{suffix}"
    index = 2
    while candidate.exists():
        candidate = OUTPUT_DIR / f"{stem}_enhanced_{index}{suffix}"
        index += 1
    return str(candidate)


class FFmpegEnhancementWorker(QObject):
    """Runs real FFmpeg-based video enhancement with actual processing."""

    started = Signal()
    progress = Signal(object)
    completed = Signal(str)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, job: ProcessingJob, duration: Optional[float]):
        super().__init__()
        self.job = job
        self.duration = duration
        self._stop = False

    def run(self):
        try:
            # Get FFmpeg path
            ffmpeg = ffmpeg_path()
            if ffmpeg is None:
                self.failed.emit(
                    "FFmpeg was not found. Install FFmpeg and add it to PATH, or place it in the app's bin/ directory."
                )
                return

            input_path = Path(self.job.input_path)
            if not input_path.exists():
                self.failed.emit(f"Input file was not found: {self.job.input_path}")
                return

            if not input_path.is_file():
                self.failed.emit(f"Input path is not a file: {self.job.input_path}")
                return

            self.started.emit()

            Path(self.job.output_path).parent.mkdir(parents=True, exist_ok=True)

            # Build FFmpeg command based on settings
            ffmpeg_args = self._build_ffmpeg_args(ffmpeg, input_path)
            
            kwargs = {
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "text": True,
                "encoding": "utf-8",
                "errors": "replace",
                "bufsize": 1,
            }
            if os.name == "nt":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

            process = subprocess.Popen(ffmpeg_args, **kwargs)

            stderr_lines = []

            def _drain_stderr():
                try:
                    if process.stderr is None:
                        return
                    for line in process.stderr:
                        stderr_lines.append(line)
                except Exception:
                    return

            drain = threading.Thread(target=_drain_stderr, daemon=True)
            drain.start()

            if self.duration is None or self.duration <= 0:
                self.progress.emit(None)

            last_percent = None
            if process.stdout is not None:
                for raw in process.stdout:
                    line = raw.strip()
                    if not line:
                        continue
                    percent = self._percent_from_progress_line(line)
                    if percent is not None and percent != last_percent:
                        last_percent = percent
                        self.progress.emit(percent)
                    if line == "progress=end":
                        break

            return_code = process.wait()
            drain.join(timeout=2)

            if return_code != 0:
                detail = "".join(stderr_lines).strip() or f"FFmpeg exited with code {return_code}."
                self.failed.emit(self._trim_error(detail))
                return

            if not output_is_valid(self.job.output_path):
                self.failed.emit("Processing finished but the output file was not created.")
                return

            if last_percent is not None:
                self.progress.emit(100)
            self.completed.emit(self.job.output_path)
        except Exception as exc:
            self.failed.emit(str(exc) or "Video processing failed.")
        finally:
            self.finished.emit()

    def _build_ffmpeg_args(self, ffmpeg: str, input_path: Path) -> list:
        """Build FFmpeg command arguments based on enhancement settings"""
        args = [
            ffmpeg,
            "-y",  # Overwrite output file
            "-hide_banner",
            "-i", str(input_path),
        ]

        # Build video filter chain based on settings
        video_filters = []
        
        # Resolution scaling
        if self.job.resolution != "Original":
            scale_filter = self._get_scale_filter(self.job.resolution)
            if scale_filter:
                video_filters.append(scale_filter)
        
        # Enhancement filters based on mode
        enhancement_filters = self._get_enhancement_filters(self.job.enhancement_mode)
        if enhancement_filters:
            video_filters.extend(enhancement_filters)
        
        # Combine video filters
        if video_filters:
            filter_complex = ",".join(video_filters)
            args.extend(["-vf", filter_complex])

        # Encoding settings based on quality mode
        codec_args = self._get_codec_args(self.job.enhancement_mode)
        args.extend(codec_args)

        # Map all streams
        args.extend(["-map", "0"])

        # Progress reporting
        args.extend(["-progress", "pipe:1", "-nostats"])

        # Output file
        args.append(self.job.output_path)

        return args

    def _get_scale_filter(self, resolution: str) -> Optional[str]:
        """Get FFmpeg scale filter for target resolution"""
        scale_map = {
            "1080p": "scale=1920:1080",
            "1440p": "scale=2560:1440", 
            "4K UHD": "scale=3840:2160",
            "8K": "scale=7680:4320",
        }
        return scale_map.get(resolution)

    def _get_enhancement_filters(self, mode: str) -> list:
        """Get enhancement filters based on quality mode"""
        filters = []
        
        if mode == "Standard":
            # Basic enhancement: slight sharpening
            filters.append("unsharp=5:5:1.0:5:5:0.5")
        elif mode == "High Quality":
            # Better enhancement: denoise + sharpen
            filters.append("hqdn3d=4:3:6")
            filters.append("unsharp=7:7:1.5:7:7:0.8")
        elif mode == "Maximum Quality":
            # Maximum enhancement: strong denoise + sharpen + color correction
            filters.append("hqdn3d=6:5:8")
            filters.append("unsharp=9:9:2.0:9:9:1.0")
            filters.append("eq=contrast=1.1:brightness=0.05:saturation=1.1")
        
        return filters

    def _get_codec_args(self, mode: str) -> list:
        """Get codec arguments based on quality mode"""
        if mode == "Standard":
            return [
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "128k"
            ]
        elif mode == "High Quality":
            return [
                "-c:v", "libx264",
                "-preset", "medium", 
                "-crf", "20",
                "-c:a", "aac",
                "-b:a", "192k"
            ]
        elif mode == "Maximum Quality":
            return [
                "-c:v", "libx264",
                "-preset", "slow",
                "-crf", "18",
                "-c:a", "aac",
                "-b:a", "256k"
            ]
        else:
            # Default to standard
            return [
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac", 
                "-b:a", "128k"
            ]

    def _percent_from_progress_line(self, line: str) -> Optional[int]:
        if self.duration is None or self.duration <= 0:
            return None
        seconds = None
        if line.startswith("out_time_ms="):
            try:
                seconds = int(line.split("=", 1)[1]) / 1000.0
            except ValueError:
                return None
        elif line.startswith("out_time_us="):
            try:
                seconds = int(line.split("=", 1)[1]) / 1_000_000.0
            except ValueError:
                return None
        elif line.startswith("out_time="):
            seconds = self._parse_timestamp(line.split("=", 1)[1])
        if seconds is None:
            return None
        return int(max(0, min(100, (seconds / self.duration) * 100)))

    def _parse_timestamp(self, value: str) -> Optional[float]:
        try:
            parts = value.split(":")
            if len(parts) != 3:
                return None
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        except ValueError:
            return None

    def _trim_error(self, detail: str) -> str:
        lines = [line.strip() for line in detail.splitlines() if line.strip()]
        useful = [line for line in lines if "error" in line.lower() or "invalid" in line.lower()]
        chosen = useful[-3:] if useful else lines[-6:]
        text = " ".join(chosen) if chosen else "FFmpeg could not process this file."
        if len(text) > 400:
            return text[:397] + "..."
        return text


class VideoProcessor(QObject):
    """UI-facing processing service. Runs FFmpeg off the GUI thread."""

    job_queued = Signal(object)
    job_started = Signal(object)
    job_progress = Signal(object, object)
    job_completed = Signal(object)
    job_failed = Signal(object, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_job: Optional[ProcessingJob] = None
        self._thread: Optional[QThread] = None
        self._worker: Optional[FFmpegEnhancementWorker] = None

    def is_busy(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def start_job(self, project: Project) -> Optional[ProcessingJob]:
        if project is None:
            return None
        if self.is_busy():
            project.error_message = "A processing job is already running."
            return None

        output_path = build_output_path(project.file_path)
        job = ProcessingJob(
            project_id=project.id,
            input_path=project.file_path,
            output_path=output_path,
            model=project.ai_model,
            resolution=project.output_resolution,
            enhancement_mode=project.enhancement_mode,
            status=ProjectStatus.QUEUED,
            progress=0,
        )
        self.current_job = job
        project.output_path = output_path
        project.progress = 0
        project.error_message = None
        project_service.queue_enhancement(project)
        self.job_queued.emit(job)

        duration = project.metadata.duration if project.metadata else None
        worker = FFmpegEnhancementWorker(job, duration)
        thread = QThread()
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.started.connect(self._on_started)
        worker.progress.connect(self._on_progress)
        worker.completed.connect(self._on_completed)
        worker.failed.connect(self._on_failed)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._on_thread_finished)

        self._thread = thread
        self._worker = worker
        thread.start()
        return job

    def _project_for_job(self) -> Optional[Project]:
        if self.current_job is None:
            return None
        return project_service.get_project_by_id(self.current_job.project_id)

    def _on_started(self):
        job = self.current_job
        if job is None:
            return
        job.status = ProjectStatus.PROCESSING
        job.started_at = datetime.now()
        job.progress = None if (self._worker and self._worker.duration is None) else job.progress
        project = self._project_for_job()
        if project is not None:
            project.update_status(ProjectStatus.PROCESSING)
            project.progress = job.progress
            project.error_message = None
        self.job_started.emit(job)

    def _on_progress(self, percent):
        job = self.current_job
        if job is None:
            return
        job.progress = percent
        project = self._project_for_job()
        if project is not None:
            project.progress = percent
        self.job_progress.emit(job, percent)

    def _on_completed(self, output_path: str):
        job = self.current_job
        if job is None:
            return
        if not output_is_valid(output_path):
            self._on_failed("Processing finished but the output file was not created.")
            return
        job.status = ProjectStatus.COMPLETED
        job.progress = 100
        job.completed_at = datetime.now()
        job.error_message = None
        project = self._project_for_job()
        if project is not None:
            project.output_path = output_path
            project.progress = 100
            project.error_message = None
            project.update_status(ProjectStatus.COMPLETED)
        self.job_completed.emit(job)

    def _on_failed(self, message: str):
        job = self.current_job
        if job is None:
            return
        job.status = ProjectStatus.FAILED
        job.completed_at = datetime.now()
        job.error_message = message
        project = self._project_for_job()
        if project is not None:
            project.error_message = message
            project.update_status(ProjectStatus.FAILED)
        self.job_failed.emit(job, message)

    def _on_thread_finished(self):
        thread = self._thread
        self._thread = None
        self._worker = None
        if thread is not None:
            thread.deleteLater()
