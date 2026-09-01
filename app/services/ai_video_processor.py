import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Optional

import cv2

from app.services.ffmpeg_tools import ffmpeg_path, ffprobe_path
from src.ai_engine.realesrgan_engine import RealESRGANEngine


APP_ROOT = Path(__file__).resolve().parents[2]


class AIVideoProcessor:
    """
    VIDEL AI video processor.

    Pipeline:
        Video
          ↓
        FFmpeg frame extraction
          ↓
        Real-ESRGAN frame-by-frame enhancement
          ↓
        FFmpeg video reconstruction
          ↓
        Original audio restored
          ↓
        Enhanced video
    """

    def __init__(
        self,
        tile: int = 512,
        outscale: int = 4,
    ):
        self.tile = tile
        self.outscale = outscale

        self.engine = RealESRGANEngine(
            tile=tile,
        )

    # ==========================================================
    # PUBLIC API
    # ==========================================================

    def upscale_video(
        self,
        input_path,
        output_path,
        progress_callback: Optional[Callable[[int], None]] = None,
    ):
        """
        Upscale an entire video using Real-ESRGAN.

        Parameters
        ----------
        input_path:
            Source video.

        output_path:
            Destination video.

        progress_callback:
            Optional callback receiving progress from 0-100.
        """

        input_path = Path(input_path)
        output_path = Path(output_path)

        if not input_path.exists():
            raise FileNotFoundError(
                f"Input video not found: {input_path}"
            )

        if not input_path.is_file():
            raise ValueError(
                f"Input path is not a file: {input_path}"
            )

        ffmpeg = ffmpeg_path()

        if ffmpeg is None:
            raise RuntimeError(
                "FFmpeg was not found."
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._report(progress_callback, 0)

        # ------------------------------------------------------
        # Get video information
        # ------------------------------------------------------

        width, height, fps, frame_count = self._probe_video(
            input_path
        )

        if width <= 0 or height <= 0:
            raise RuntimeError(
                "Could not determine video dimensions."
            )

        if fps <= 0:
            fps = 30.0

        if frame_count <= 0:
            raise RuntimeError(
                "Could not determine video frame count."
            )

        print()
        print("=" * 60)
        print("VIDEL - AI VIDEO UPSCALING")
        print("=" * 60)
        print(f"Input      : {input_path}")
        print(f"Resolution : {width}x{height}")
        print(f"FPS        : {fps:.3f}")
        print(f"Frames     : {frame_count}")
        print(f"Scale      : {self.outscale}x")
        print(f"Output     : {output_path}")
        print("=" * 60)

        # ------------------------------------------------------
        # Temporary workspace
        # ------------------------------------------------------

        temp_root = APP_ROOT / "temp"
        temp_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        with tempfile.TemporaryDirectory(
            prefix="videl_ai_",
            dir=str(temp_root),
        ) as temp_dir:

            temp_dir = Path(temp_dir)

            input_frames = temp_dir / "input_frames"
            output_frames = temp_dir / "output_frames"

            input_frames.mkdir()
            output_frames.mkdir()

            # --------------------------------------------------
            # 1. Extract frames
            # --------------------------------------------------

            print()
            print("Step 1/3 - Extracting video frames...")

            self._extract_frames(
                ffmpeg=ffmpeg,
                input_path=input_path,
                frame_directory=input_frames,
            )

            frames = sorted(
                input_frames.glob("frame_*.png")
            )

            if not frames:
                raise RuntimeError(
                    "FFmpeg did not extract any video frames."
                )

            actual_frame_count = len(frames)

            print(
                f"Extracted {actual_frame_count} frames."
            )

            # --------------------------------------------------
            # 2. AI enhancement
            # --------------------------------------------------

            print()
            print("Step 2/3 - Running Real-ESRGAN...")

            for index, frame_path in enumerate(
                frames,
                start=1,
            ):

                output_frame = (
                    output_frames
                    / f"frame_{index:08d}.png"
                )

                self._process_frame(
                    frame_path,
                    output_frame,
                )

                percent = int(
                    (index / actual_frame_count) * 100
                )

                # AI stage occupies 10-90%
                overall_progress = (
                    10 + int(percent * 0.8)
                )

                self._report(
                    progress_callback,
                    overall_progress,
                )

                if index == 1 or index % 10 == 0:
                    print(
                        f"AI frame {index}/{actual_frame_count} "
                        f"({percent}%)"
                    )

            # --------------------------------------------------
            # 3. Reconstruct video
            # --------------------------------------------------

            print()
            print("Step 3/3 - Rebuilding enhanced video...")

            self._report(
                progress_callback,
                92,
            )

            self._rebuild_video(
                ffmpeg=ffmpeg,
                ffprobe=ffprobe_path(),
                input_path=input_path,
                output_path=output_path,
                frame_directory=output_frames,
                fps=fps,
            )

            self._report(
                progress_callback,
                100,
            )

        print()
        print("=" * 60)
        print("AI VIDEO UPSCALING COMPLETE")
        print("=" * 60)
        print(f"Output: {output_path}")
        print("=" * 60)

        return output_path

    # ==========================================================
    # FRAME PROCESSING
    # ==========================================================

    def _process_frame(
        self,
        input_frame: Path,
        output_frame: Path,
    ):
        """
        Process one video frame using Real-ESRGAN.

        We intentionally process one frame at a time
        to keep RAM usage manageable on CPU systems.
        """

        image = cv2.imread(
            str(input_frame),
            cv2.IMREAD_COLOR,
        )

        if image is None:
            raise RuntimeError(
                f"Could not read frame: {input_frame}"
            )

        output, _ = self.engine.upsampler.enhance(
            image,
            outscale=self.outscale,
        )

        success = cv2.imwrite(
            str(output_frame),
            output,
        )

        if not success:
            raise IOError(
                f"Could not save enhanced frame: "
                f"{output_frame}"
            )

    # ==========================================================
    # FRAME EXTRACTION
    # ==========================================================

    def _extract_frames(
        self,
        ffmpeg: str,
        input_path: Path,
        frame_directory: Path,
    ):
        frame_pattern = (
            frame_directory
            / "frame_%08d.png"
        )

        command = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(input_path),
            "-vsync",
            "0",
            str(frame_pattern),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if hasattr(
                    subprocess,
                    "CREATE_NO_WINDOW",
                )
                else 0
            ),
        )

        if result.returncode != 0:
            raise RuntimeError(
                "FFmpeg frame extraction failed:\n"
                + result.stderr.strip()
            )

    # ==========================================================
    # VIDEO RECONSTRUCTION
    # ==========================================================

    def _rebuild_video(
        self,
        ffmpeg: str,
        ffprobe: Optional[str],
        input_path: Path,
        output_path: Path,
        frame_directory: Path,
        fps: float,
    ):
        frame_pattern = (
            frame_directory
            / "frame_%08d.png"
        )

        temp_video = (
            output_path.parent
            / f"{output_path.stem}_video_only"
            f"{output_path.suffix}"
        )

        try:
            # --------------------------------------------------
            # Encode enhanced frames
            # --------------------------------------------------

            command = [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",

                "-framerate",
                self._format_fps(fps),

                "-i",
                str(frame_pattern),

                "-c:v",
                "libx264",

                "-preset",
                "medium",

                "-crf",
                "18",

                "-pix_fmt",
                "yuv420p",

                str(temp_video),
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if hasattr(
                        subprocess,
                        "CREATE_NO_WINDOW",
                    )
                    else 0
                ),
            )

            if result.returncode != 0:
                raise RuntimeError(
                    "FFmpeg video reconstruction failed:\n"
                    + result.stderr.strip()
                )

            # --------------------------------------------------
            # Restore original audio
            # --------------------------------------------------

            command = [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",

                "-i",
                str(temp_video),

                "-i",
                str(input_path),

                "-map",
                "0:v:0",

                "-map",
                "1:a?",

                "-c:v",
                "copy",

                "-c:a",
                "aac",

                "-b:a",
                "192k",

                "-shortest",

                str(output_path),
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if hasattr(
                        subprocess,
                        "CREATE_NO_WINDOW",
                    )
                    else 0
                ),
            )

            if result.returncode != 0:
                raise RuntimeError(
                    "FFmpeg audio restoration failed:\n"
                    + result.stderr.strip()
                )

        finally:
            if temp_video.exists():
                try:
                    temp_video.unlink()
                except OSError:
                    pass

    # ==========================================================
    # VIDEO PROBING
    # ==========================================================

    def _probe_video(
        self,
        input_path: Path,
    ):
        ffprobe = ffprobe_path()

        if ffprobe is None:
            return self._probe_with_opencv(
                input_path
            )

        command = [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate,nb_frames",
            "-of",
            "default=noprint_wrappers=1",
            str(input_path),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if hasattr(
                    subprocess,
                    "CREATE_NO_WINDOW",
                )
                else 0
            ),
        )

        if result.returncode != 0:
            return self._probe_with_opencv(
                input_path
            )

        values = {}

        for line in result.stdout.splitlines():
            if "=" in line:
                key, value = line.split(
                    "=",
                    1,
                )
                values[key.strip()] = value.strip()

        try:
            width = int(
                values.get("width", 0)
            )

            height = int(
                values.get("height", 0)
            )

            fps = self._parse_fps(
                values.get("r_frame_rate")
            )

            frame_count = int(
                values.get("nb_frames", 0)
                or 0
            )

            if frame_count <= 0:
                return self._probe_with_opencv(
                    input_path
                )

            return (
                width,
                height,
                fps,
                frame_count,
            )

        except (
            TypeError,
            ValueError,
        ):
            return self._probe_with_opencv(
                input_path
            )

    def _probe_with_opencv(
        self,
        input_path: Path,
    ):
        cap = cv2.VideoCapture(
            str(input_path)
        )

        if not cap.isOpened():
            raise RuntimeError(
                f"Could not open video: {input_path}"
            )

        width = int(
            cap.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
            or 0
        )

        height = int(
            cap.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
            or 0
        )

        fps = float(
            cap.get(
                cv2.CAP_PROP_FPS
            )
            or 0
        )

        frame_count = int(
            cap.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
            or 0
        )

        cap.release()

        return (
            width,
            height,
            fps,
            frame_count,
        )

    # ==========================================================
    # HELPERS
    # ==========================================================

    @staticmethod
    def _parse_fps(value) -> float:
        if not value:
            return 0.0

        text = str(value)

        if "/" in text:
            numerator, denominator = (
                text.split("/", 1)
            )

            denominator = float(
                denominator
            )

            if denominator == 0:
                return 0.0

            return (
                float(numerator)
                / denominator
            )

        return float(text)

    @staticmethod
    def _format_fps(fps: float) -> str:
        return f"{fps:.06f}"

    @staticmethod
    def _report(
        callback,
        value: int,
    ):
        if callback is None:
            return

        value = max(
            0,
            min(100, int(value)),
        )

        callback(value)