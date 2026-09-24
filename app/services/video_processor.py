import os
import subprocess
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
    """Runs Real-ESRGAN NCNN Vulkan video enhancement."""

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

        self.app_root = Path(__file__).resolve().parents[2]

        self.ncnn_dir = self.app_root / "engines" / "realesrgan-ncnn-vulkan"

        self.ncnn_exe = self.ncnn_dir / "realesrgan-ncnn-vulkan.exe"

        # Reliable model for real-life footage.
        self.model_name = "realesrgan-x4plus"

        # Intel HD 620 works more reliably with a smaller tile.
        self.tile = 128

        # --------------------------------------------------
        # Optional short test mode
        #
        # Set VIDEL_TEST_FRAMES in PowerShell to limit the
        # number of frames processed during development.
        #
        # Example:
        # $env:VIDEL_TEST_FRAMES="5"
        # --------------------------------------------------

        test_frames = os.environ.get("VIDEL_TEST_FRAMES")

        try:
            self.test_max_frames = int(test_frames) if test_frames else None
        except ValueError:
            self.test_max_frames = None

    def run(self):
        try:
            ffmpeg = ffmpeg_path()

            if ffmpeg is None:
                self.failed.emit(
                    "FFmpeg was not found. Install FFmpeg and add it "
                    "to PATH, or place it in the app's bin/ directory."
                )
                return

            input_path = Path(self.job.input_path)

            if not input_path.exists():
                self.failed.emit(f"Input file was not found: {input_path}")
                return

            if not input_path.is_file():
                self.failed.emit(f"Input path is not a file: {input_path}")
                return

            if not self.ncnn_exe.exists():
                self.failed.emit(
                    "Real-ESRGAN NCNN Vulkan engine was not found.\n\n"
                    f"Expected:\n{self.ncnn_exe}"
                )
                return

            if not self.ncnn_dir.exists():
                self.failed.emit("Real-ESRGAN engine directory was not found.")
                return

            self.started.emit()

            output_path = Path(self.job.output_path)
            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            fps = self._get_video_fps(
                ffmpeg,
                input_path,
            )

            print("=" * 70)
            print("VIDEL - AI VIDEO UPSCALING")
            print("=" * 70)
            print(f"Input       : {input_path}")
            print(f"Output      : {output_path}")
            print(f"Model       : {self.model_name}")
            ai_scale = 2 if self.job.resolution in ("Original", "2×") else 4
            print(f"AI Scale    : {ai_scale}x")
            print(f"Output Scale: {self.job.resolution}")
            print(f"Tile        : {self.tile}")
            print(f"FPS         : {fps:.3f}")

            if self.test_max_frames is not None:
                print(f"TEST MODE   : first " f"{self.test_max_frames} frame(s)")

            print("=" * 70)

            import tempfile

            with tempfile.TemporaryDirectory(prefix="videl_ai_") as temp_dir:

                temp_dir = Path(temp_dir)

                frames_dir = temp_dir / "frames"
                enhanced_dir = temp_dir / "enhanced"
                scaled_dir = temp_dir / "scaled"

                frames_dir.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                enhanced_dir.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                scaled_dir.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                # --------------------------------------------------
                # 1. Extract frames
                # --------------------------------------------------

                print("\n[1/4] Extracting video frames...")

                self._extract_frames(
                    ffmpeg=ffmpeg,
                    input_path=input_path,
                    frames_dir=frames_dir,
                )

                frames = sorted(frames_dir.glob("frame_*.png"))

                # Limit frames during development/testing.
                if self.test_max_frames is not None:
                    frames_to_remove = frames[self.test_max_frames :]

                    for frame_path in frames_to_remove:
                        frame_path.unlink(missing_ok=True)

                    frames = frames[: self.test_max_frames]

                    print(f"TEST MODE: processing only " f"{len(frames)} frame(s).")

                if not frames:
                    raise RuntimeError("FFmpeg did not extract any video frames.")

                total_frames = len(frames)

                print(f"Extracted {total_frames} frames.")

                # --------------------------------------------------
                # 2. Real-ESRGAN x4plus / Vulkan
                # --------------------------------------------------

                print("\n[2/4] Running Real-ESRGAN NCNN Vulkan...")

                if self._stop:
                    raise RuntimeError("Video processing was stopped.")

                self._enhance_frames_batch(
                    frames_dir=frames_dir,
                    enhanced_dir=enhanced_dir,
                )

                enhanced_frames = sorted(enhanced_dir.glob("frame_*.png"))

                if len(enhanced_frames) != total_frames:
                    raise RuntimeError(
                        "Real-ESRGAN did not produce the expected number of frames.\n"
                        f"Expected: {total_frames}\n"
                        f"Created: {len(enhanced_frames)}"
                    )

                print(f"AI completed: {len(enhanced_frames)}/{total_frames} frames.")
                self.progress.emit(75)

                # --------------------------------------------------
                # 3. Scale output
                # --------------------------------------------------

                print("\n[3/4] Applying output scaling...")

                self._scale_frames(
                    ffmpeg=ffmpeg,
                    enhanced_dir=enhanced_dir,
                    scaled_dir=scaled_dir,
                )

                self.progress.emit(90)

                # --------------------------------------------------
                # 4. Rebuild video
                # --------------------------------------------------

                print("\n[4/4] Rebuilding video...")

                self._rebuild_video(
                    ffmpeg=ffmpeg,
                    input_path=input_path,
                    scaled_dir=scaled_dir,
                    output_path=output_path,
                    fps=fps,
                )

                self.progress.emit(100)

            print("\n" + "=" * 70)
            print("VIDEL - AI VIDEO UPSCALING COMPLETE")
            print("=" * 70)
            print(f"Saved: {output_path}")
            print("=" * 70)

            self.completed.emit(str(output_path))

        except Exception as exc:
            self.failed.emit(str(exc) or "Video processing failed.")

        finally:
            self.finished.emit()

    def _enhance_frame(
        self,
        input_frame: Path,
        output_frame: Path,
    ):
        """Run Real-ESRGAN x4plus through NCNN Vulkan."""
        ai_scale = 2 if self.job.resolution in ("Original", "2×") else 4

        command = [
            str(self.ncnn_exe),
            "-i",
            str(input_frame),
            "-o",
            str(output_frame),
            "-n",
            self.model_name,
            "-s",
            str(ai_scale),
            "-t",
            str(self.tile),
            "-g",
            "0",
            "-f",
            "png",
            "-v",
        ]

        kwargs = {
            "cwd": str(self.ncnn_dir),
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
        }

        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            command,
            **kwargs,
        )

        if result.returncode != 0:
            detail = (
                result.stderr.strip()
                or result.stdout.strip()
                or ("NCNN exited with code " f"{result.returncode}.")
            )

            raise RuntimeError("Real-ESRGAN Vulkan failed:\n" + detail)

        if not output_frame.exists():
            raise RuntimeError(
                "Real-ESRGAN completed but did not create:\n" f"{output_frame}"
            )

        if output_frame.stat().st_size <= 0:
            raise RuntimeError(
                "Real-ESRGAN created an empty frame:\n" f"{output_frame}"
            )

    def _scale_frames(
        self,
        ffmpeg: str,
        enhanced_dir: Path,
        scaled_dir: Path,
    ):
        """Convert AI output to the requested final output scale."""

        frames = sorted(enhanced_dir.glob("frame_*.png"))

        if not frames:
            raise RuntimeError("No enhanced frames were produced.")

        total_frames = len(frames)

        for index, frame_path in enumerate(frames):

            if self._stop:
                raise RuntimeError("Video processing was stopped.")

            output_frame = scaled_dir / frame_path.name

            scale_filter = self._get_output_scale_filter()

            # --------------------------------------------------
            # No resize required
            #
            # For 2x and 4x output, Real-ESRGAN already produced
            # the correct final resolution. Simply move the
            # enhanced PNG into the scaled directory.
            # --------------------------------------------------
            if scale_filter is None:
                try:
                    os.replace(frame_path, output_frame)
                except OSError as exc:
                    raise RuntimeError(
                        "Could not move enhanced frame to scaled directory:\n"
                        f"{frame_path}\n\n"
                        f"Error: {exc}"
                    ) from exc

            # --------------------------------------------------
            # Resize required
            #
            # Used for:
            # Original -> AI creates 2x, then resize to 1x
            # 3x       -> AI creates 4x, then resize to 3x
            # --------------------------------------------------
            else:
                command = [
                    ffmpeg,
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-i",
                    str(frame_path),
                    "-vf",
                    scale_filter,
                    "-frames:v",
                    "1",
                    "-update",
                    "1",
                    str(output_frame),
                ]

                kwargs = {
                    "capture_output": True,
                    "text": True,
                    "encoding": "utf-8",
                    "errors": "replace",
                }

                if os.name == "nt":
                    kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

                result = subprocess.run(
                    command,
                    **kwargs,
                )

                if result.returncode != 0:
                    raise RuntimeError(
                        "FFmpeg scaling failed:\n" + result.stderr
                    )

                if not output_frame.exists():
                    raise RuntimeError(
                        "Scaled frame was not created:\n"
                        f"{output_frame}"
                    )

                if output_frame.stat().st_size <= 0:
                    raise RuntimeError(
                        "FFmpeg created an empty scaled frame:\n"
                        f"{output_frame}"
                    )

            # Scaling stage occupies 75-90%.
            percent = 75 + int(
                ((index + 1) / total_frames) * 15
            )

            self.progress.emit(percent)

            if (
                index == 0
                or (index + 1) % 5 == 0
                or index == total_frames - 1
            ):
                print(
                    f"Scaling progress: "
                    f"{index + 1}/{total_frames} "
                    f"({percent}%)"
                )

    def _get_output_scale_filter(self) -> Optional[str]:
        """
        Determine whether the AI frame needs resizing.

        AI processing:
            Original -> 2x AI
            2x       -> 2x AI
            3x       -> 4x AI
            4x       -> 4x AI

        Resize only when the AI output does not already match
        the requested output scale.
        """

        resolution = self.job.resolution

        if resolution == "Original":
            scale = "scale=iw/2:" "ih/2:" "flags=lanczos+accurate_rnd"
        elif resolution == "2×":
            return None
        elif resolution == "3×":
            scale = "scale=iw*3/4:" "ih*3/4:" "flags=lanczos+accurate_rnd"
        elif resolution == "4×":
            return None
        else:
            return None

        return f"{scale}," "unsharp=5:5:0.25:5:5:0"

    def _extract_frames(
        self,
        ffmpeg: str,
        input_path: Path,
        frames_dir: Path,
    ):
        """Extract source frames without changing source FPS."""

        frame_pattern = frames_dir / "frame_%08d.png"

        command = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(input_path),
            "-fps_mode",
            "passthrough",
            str(frame_pattern),
        ]

        kwargs = {
            "capture_output": True,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
        }

        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            command,
            **kwargs,
        )

        if result.returncode != 0:
            raise RuntimeError("FFmpeg frame extraction failed:\n" + result.stderr)

    def _get_video_fps(
        self,
        ffmpeg: str,
        input_path: Path,
    ) -> float:
        """Read the source video's original frame rate."""

        ffprobe = Path(ffmpeg).with_name("ffprobe.exe")

        if not ffprobe.exists():
            discovered = ffprobe_path()

            if discovered is None:
                raise RuntimeError(
                    "FFprobe was not found. "
                    "FFprobe is required to preserve "
                    "the original video's frame rate."
                )

            ffprobe = Path(discovered)

        command = [
            str(ffprobe),
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=r_frame_rate",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(input_path),
        ]

        kwargs = {
            "capture_output": True,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
        }

        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            command,
            **kwargs,
        )

        if result.returncode != 0:
            raise RuntimeError("Could not determine video FPS:\n" + result.stderr)

        fps_string = result.stdout.strip()

        if not fps_string:
            raise RuntimeError("FFprobe returned no FPS information.")

        try:
            if "/" in fps_string:
                numerator, denominator = fps_string.split("/", 1)

                numerator = float(numerator)
                denominator = float(denominator)

                if denominator == 0:
                    raise ValueError("FPS denominator is zero.")

                fps = numerator / denominator

            else:
                fps = float(fps_string)

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise RuntimeError(
                "Invalid FPS returned by FFprobe: " f"{fps_string}"
            ) from exc

        if fps <= 0:
            raise RuntimeError(f"Invalid video FPS: {fps}")

        return fps

    def _rebuild_video(
        self,
        ffmpeg: str,
        input_path: Path,
        scaled_dir: Path,
        output_path: Path,
        fps: float,
    ):
        """Rebuild the enhanced video and preserve audio."""

        frame_pattern = scaled_dir / "frame_%08d.png"

        command = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-framerate",
            str(fps),
            "-i",
            str(frame_pattern),
            "-i",
            str(input_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a?",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(output_path),
        ]

        kwargs = {
            "capture_output": True,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
        }

        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            command,
            **kwargs,
        )

        if result.returncode != 0:
            raise RuntimeError("FFmpeg video reconstruction failed:\n" + result.stderr)

        if not output_path.exists():
            raise RuntimeError(
                "FFmpeg finished but the output video " "was not created."
            )

        if output_path.stat().st_size <= 0:
            raise RuntimeError("FFmpeg created an empty output video.")


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

    def start_job(
        self,
        project: Project,
    ) -> Optional[ProcessingJob]:

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

        worker = FFmpegEnhancementWorker(
            job,
            duration,
        )

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

    def _project_for_job(
        self,
    ) -> Optional[Project]:

        if self.current_job is None:
            return None

        return project_service.get_project_by_id(self.current_job.project_id)

    def _on_started(self):

        job = self.current_job

        if job is None:
            return

        job.status = ProjectStatus.PROCESSING
        job.started_at = datetime.now()

        job.progress = (
            None if (self._worker and self._worker.duration is None) else job.progress
        )

        project = self._project_for_job()

        if project is not None:
            project.update_status(ProjectStatus.PROCESSING)

            project.progress = job.progress
            project.error_message = None

        self.job_started.emit(job)

    def _on_progress(
        self,
        percent,
    ):

        job = self.current_job

        if job is None:
            return

        job.progress = percent

        project = self._project_for_job()

        if project is not None:
            project.progress = percent

        self.job_progress.emit(
            job,
            percent,
        )

    def _on_completed(
        self,
        output_path: str,
    ):

        job = self.current_job

        if job is None:
            return

        if not output_is_valid(output_path):
            self._on_failed(
                "Processing finished but the output " "file was not created."
            )
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

    def _on_failed(
        self,
        message: str,
    ):

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

        self.job_failed.emit(
            job,
            message,
        )

    def _on_thread_finished(self):

        thread = self._thread

        self._thread = None
        self._worker = None

        if thread is not None:
            thread.deleteLater()
