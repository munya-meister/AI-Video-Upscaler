import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Optional

from src.ai_engine.realesrgan_engine import RealESRGANEngine
from app.services.ffmpeg_tools import ffmpeg_path


class AIVideoProcessor:
    """
    Real-ESRGAN video upscaling pipeline.

    Pipeline:

        Video
          ↓
        FFmpeg frame extraction
          ↓
        Real-ESRGAN
          ↓
        Enhanced frames
          ↓
        FFmpeg video reconstruction
          ↓
        Final MP4

    Important:
        The original video's FPS is detected with FFprobe and
        reused when rebuilding the enhanced video. This prevents
        the output from becoming slow motion.
    """

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(
        self,
        model_path=None,
        tile=256,
    ):
        self.engine = RealESRGANEngine(
            model_path=model_path,
            scale=4,
            tile=tile,
        )

    # ==========================================================
    # PUBLIC API
    # ==========================================================

    def upscale_video(
    self,
    input_path,
    output_path,
    outscale=2,
    progress_callback: Optional[Callable[[int], None]] = None,
    max_frames: Optional[int] = None,
    ):
        """
        Upscale a complete video using Real-ESRGAN.

        The original FPS is preserved.
        """

        input_path = Path(input_path)
        output_path = Path(output_path)

        # ------------------------------------------------------
        # Validate input
        # ------------------------------------------------------

        if not input_path.exists():
            raise FileNotFoundError(
                f"Input video not found: {input_path}"
            )

        if not input_path.is_file():
            raise ValueError(
                f"Input path is not a file: {input_path}"
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ------------------------------------------------------
        # Locate FFmpeg
        # ------------------------------------------------------

        ffmpeg = self._find_ffmpeg()

        if ffmpeg is None:
            raise RuntimeError(
                "FFmpeg was not found. "
                "Make sure FFmpeg is installed and available "
                "through VIDEL's FFmpeg discovery system."
            )

        # ------------------------------------------------------
        # Detect original FPS
        # ------------------------------------------------------

        fps = self._get_video_fps(
            ffmpeg,
            input_path,
        )

        print("=" * 60)
        print("VIDEL - AI VIDEO UPSCALING")
        print("=" * 60)
        print(f"Input : {input_path}")
        print(f"Output: {output_path}")
        print("Model : RealESRGAN_x4plus")
        print(f"Scale : {outscale}x")
        print(f"FPS   : {fps:.3f}")
        print("=" * 60)

        # ------------------------------------------------------
        # Temporary working directory
        # ------------------------------------------------------

        with tempfile.TemporaryDirectory(
            prefix="videl_ai_"
        ) as temp_dir:

            temp_dir = Path(temp_dir)

            frames_dir = temp_dir / "frames"
            enhanced_dir = temp_dir / "enhanced"

            frames_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            enhanced_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            # ==================================================
            # 1. EXTRACT FRAMES
            # ==================================================

            print("\n[1/3] Extracting video frames...")

            self._extract_frames(
                ffmpeg=ffmpeg,
                input_path=input_path,
                frames_dir=frames_dir,
            )

            frames = sorted(
                frames_dir.glob("frame_*.png")
            )
            if max_frames is not None:
             frames = frames[:max_frames]

            if not frames:
                raise RuntimeError(
                    "FFmpeg did not extract any video frames."
                )

            total_frames = len(frames)

            print(
                f"Extracted {total_frames} frames."
            )

            # ==================================================
            # 2. AI ENHANCEMENT
            # ==================================================

            print("\n[2/3] Running Real-ESRGAN...")

            for index, frame_path in enumerate(frames):

                output_frame = (
                    enhanced_dir
                    / frame_path.name
                )

                self.engine.upscale_image(
                    frame_path,
                    output_frame,
                    outscale=outscale,
                )

                percent = int(
                    ((index + 1) / total_frames) * 100
                )

                if progress_callback:
                    progress_callback(percent)

                # Print progress every 10 frames
                # and always print first/last frame.
                if (
                    index == 0
                    or (index + 1) % 10 == 0
                    or index == total_frames - 1
                ):
                    print(
                        f"AI progress: "
                        f"{index + 1}/{total_frames} "
                        f"({percent}%)"
                    )

            # ==================================================
            # 3. REBUILD VIDEO
            # ==================================================

            print("\n[3/3] Rebuilding video...")

            self._rebuild_video(
                ffmpeg=ffmpeg,
                input_path=input_path,
                enhanced_dir=enhanced_dir,
                output_path=output_path,
                fps=fps,
            )

        # ======================================================
        # COMPLETE
        # ======================================================

        print("\n" + "=" * 60)
        print("AI VIDEO UPSCALING COMPLETE")
        print("=" * 60)
        print(f"Saved: {output_path}")

        if progress_callback:
            progress_callback(100)

        return output_path

    # ==========================================================
    # FFMPEG DISCOVERY
    # ==========================================================

    def _find_ffmpeg(self):
        """
        Locate FFmpeg using VIDEL's central FFmpeg discovery
        system.
        """

        return ffmpeg_path()

    # ==========================================================
    # FPS DETECTION
    # ==========================================================

    def _get_video_fps(
        self,
        ffmpeg,
        input_path,
    ):
        """
        Get the original video's frame rate using FFprobe.

        Examples of values FFprobe may return:

            30/1
            60/1
            30000/1001
            24000/1001
        """

        ffprobe = Path(
            ffmpeg
        ).with_name("ffprobe.exe")

        # ------------------------------------------------------
        # Check FFprobe
        # ------------------------------------------------------

        if not ffprobe.exists():

            # Try the central VIDEL FFprobe discovery system.
            from app.services.ffmpeg_tools import ffprobe_path

            discovered_ffprobe = ffprobe_path()

            if discovered_ffprobe is None:
                raise RuntimeError(
                    "FFprobe was not found. "
                    "FFprobe is required to preserve the "
                    "original video's frame rate."
                )

            ffprobe = Path(
                discovered_ffprobe
            )

        # ------------------------------------------------------
        # FFprobe command
        # ------------------------------------------------------

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

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:

            raise RuntimeError(
                "Could not determine video FPS:\n"
                + result.stderr
            )

        fps_string = result.stdout.strip()

        if not fps_string:

            raise RuntimeError(
                "FFprobe returned no FPS information."
            )

        # ------------------------------------------------------
        # Parse FPS
        # ------------------------------------------------------

        try:

            if "/" in fps_string:

                numerator, denominator = (
                    fps_string.split("/", 1)
                )

                numerator = float(
                    numerator
                )

                denominator = float(
                    denominator
                )

                if denominator == 0:

                    raise ValueError(
                        "FPS denominator is zero."
                    )

                fps = numerator / denominator

            else:

                fps = float(
                    fps_string
                )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise RuntimeError(
                f"Invalid FPS returned by FFprobe: "
                f"{fps_string}"
            ) from exc

        if fps <= 0:

            raise RuntimeError(
                f"Invalid video FPS: {fps}"
            )

        return fps

    # ==========================================================
    # FRAME EXTRACTION
    # ==========================================================

    def _extract_frames(
        self,
        ffmpeg,
        input_path,
        frames_dir,
    ):
        """
        Extract every video frame as a PNG.

        No FPS conversion is performed here.
        """

        frame_pattern = (
            frames_dir
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

            # Keep the original frame timing.
            "-fps_mode",
            "passthrough",

            str(frame_pattern),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:

            raise RuntimeError(
                "FFmpeg frame extraction failed:\n"
                + result.stderr
            )

    # ==========================================================
    # VIDEO REBUILD
    # ==========================================================

    def _rebuild_video(
        self,
        ffmpeg,
        input_path,
        enhanced_dir,
        output_path,
        fps,
    ):
        """
        Rebuild the video from enhanced frames.

        IMPORTANT:
            Uses the ORIGINAL FPS instead of hardcoding
            30 FPS. This prevents slow-motion output.
        """

        frame_pattern = (
            enhanced_dir
            / "frame_%08d.png"
        )

        command = [
            ffmpeg,

            "-y",

            "-hide_banner",

            "-loglevel",
            "error",

            # --------------------------------------------------
            # Enhanced frames
            # --------------------------------------------------

            "-framerate",
            str(fps),

            "-i",
            str(frame_pattern),

            # --------------------------------------------------
            # Original video
            # --------------------------------------------------

            "-i",
            str(input_path),

            # --------------------------------------------------
            # Video encoder
            # --------------------------------------------------

            "-c:v",
            "libx264",

            "-preset",
            "medium",

            "-crf",
            "18",

            "-pix_fmt",
            "yuv420p",

            # --------------------------------------------------
            # Audio
            # --------------------------------------------------

            "-c:a",
            "aac",

            "-b:a",
            "192k",

            # --------------------------------------------------
            # Stream mapping
            # --------------------------------------------------

            "-map",
            "0:v:0",

            "-map",
            "1:a?",

            # --------------------------------------------------
            # Keep video/audio duration aligned
            # --------------------------------------------------

            "-shortest",

            # --------------------------------------------------
            # Output
            # --------------------------------------------------

            str(output_path),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:

            raise RuntimeError(
                "FFmpeg video reconstruction failed:\n"
                + result.stderr
            )

        # ------------------------------------------------------
        # Validate output
        # ------------------------------------------------------

        if not output_path.exists():

            raise RuntimeError(
                "FFmpeg finished but the output video "
                "was not created."
            )

        if output_path.stat().st_size <= 0:

            raise RuntimeError(
                "FFmpeg created an empty output video."
            )