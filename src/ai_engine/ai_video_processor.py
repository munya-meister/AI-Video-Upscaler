import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Optional

from app.services.ffmpeg_tools import ffmpeg_path


class AIVideoProcessor:
    """
    VIDEL Natural Video Enhancement Engine.

    Processing pipeline:

        Input Video
             ↓
        FFmpeg frame extraction
             ↓
        Real-ESRGAN x4plus
        NCNN Vulkan GPU
             ↓
        4× AI enhanced frame
             ↓
        Lanczos downsampling
             ↓
        Natural sharpening
             ↓
        FFmpeg video reconstruction
             ↓
        Original audio restored

    The AI engine always performs 4× enhancement internally.

    Requested output scale controls the final resize:

        1× → 4× AI → downsample to 1×
        2× → 4× AI → downsample to 2×
        3× → 4× AI → downsample to 3×
        4× → 4× AI → keep 4×

    This allows VIDEL to use the stronger x4plus model while
    producing controlled final output sizes.
    """

    # ==========================================================
    # CONFIGURATION
    # ==========================================================

    AI_MODEL = "realesrgan-x4plus"

    AI_SCALE = 4

    # Proven stable setting on the Intel HD 620.
    AI_TILE = 128

    # Mild sharpening applied AFTER Lanczos reduction.
    # This is deliberately conservative to avoid waxy/crunchy skin.
    SHARPEN_FILTER = (
        "unsharp=5:5:0.25:5:5:0"
    )

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(
        self,
        model_path=None,
        tile=128,
    ):
        """
        Initialize the video processor.

        model_path is retained for API compatibility with the
        previous implementation.

        NCNN uses its own model directory located beside the
        realesrgan-ncnn-vulkan executable.
        """

        self.model_path = model_path
        self.tile = tile if tile is not None else self.AI_TILE

        self.ncnn_executable = self._find_ncnn_executable()

        if self.ncnn_executable is None:
            raise RuntimeError(
                "VIDEL could not find the Real-ESRGAN NCNN Vulkan "
                "executable.\n\n"
                "Expected:\n"
                "engines\\realesrgan-ncnn-vulkan\\"
                "realesrgan-ncnn-vulkan.exe"
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
        Upscale a video using Real-ESRGAN NCNN Vulkan.

        Parameters
        ----------
        input_path:
            Source video.

        output_path:
            Final video path.

        outscale:
            Requested final scale: 1, 2, 3 or 4.

        progress_callback:
            Optional callback receiving integer progress 0-100.

        max_frames:
            Optional frame limit useful for testing.
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

        # ------------------------------------------------------
        # Validate scale
        # ------------------------------------------------------

        try:
            outscale = int(outscale)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid output scale: {outscale}"
            ) from exc

        if outscale not in (1, 2, 3, 4):
            raise ValueError(
                "VIDEL currently supports output scales "
                "of 1×, 2×, 3× or 4×."
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
        # Detect source FPS
        # ------------------------------------------------------

        fps = self._get_video_fps(
            ffmpeg,
            input_path,
        )

        # ------------------------------------------------------
        # Print processing information
        # ------------------------------------------------------

        print("=" * 70)
        print("VIDEL - NATURAL AI VIDEO ENHANCEMENT")
        print("=" * 70)
        print(f"Input       : {input_path}")
        print(f"Output      : {output_path}")
        print(f"AI Model    : {self.AI_MODEL}")
        print(f"AI Scale    : {self.AI_SCALE}x")
        print(f"Output Scale: {outscale}x")
        print(f"Tile        : {self.tile}")
        print(f"FPS         : {fps:.3f}")
        print(f"Vulkan GPU  : Intel / NCNN Vulkan")
        print("=" * 70)

        self._report_progress(
            progress_callback,
            0,
        )

        # ------------------------------------------------------
        # Temporary working directory
        # ------------------------------------------------------

        with tempfile.TemporaryDirectory(
            prefix="videl_ai_"
        ) as temp_dir:

            temp_dir = Path(temp_dir)

            frames_dir = temp_dir / "frames"
            enhanced_dir = temp_dir / "enhanced"
            final_frames_dir = temp_dir / "final"

            frames_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            enhanced_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            final_frames_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            # ==================================================
            # 1. EXTRACT FRAMES
            # ==================================================

            print("\n[1/4] Extracting original video frames...")

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

            self._report_progress(
                progress_callback,
                5,
            )

            # ==================================================
            # 2. REAL-ESRGAN NCNN VULKAN
            # ==================================================

            print(
                "\n[2/4] Running Real-ESRGAN x4plus "
                "through NCNN Vulkan..."
            )

            for index, frame_path in enumerate(frames):

                enhanced_frame = (
                    enhanced_dir
                    / frame_path.name
                )

                self._upscale_frame_ncnn(
                    input_frame=frame_path,
                    output_frame=enhanced_frame,
                )

                # AI stage occupies 5-80%.
                ai_percent = int(
                    5
                    + (
                        (index + 1)
                        / total_frames
                    )
                    * 75
                )

                self._report_progress(
                    progress_callback,
                    ai_percent,
                )

                if (
                    index == 0
                    or (index + 1) % 5 == 0
                    or index == total_frames - 1
                ):
                    print(
                        f"AI progress: "
                        f"{index + 1}/{total_frames} "
                        f"({ai_percent}%)"
                    )

            # ==================================================
            # 3. OUTPUT SCALING + NATURAL SHARPENING
            # ==================================================

            print(
                "\n[3/4] Creating final output frames..."
            )

            for index, frame_path in enumerate(frames):

                enhanced_frame = (
                    enhanced_dir
                    / frame_path.name
                )

                final_frame = (
                    final_frames_dir
                    / frame_path.name
                )

                self._prepare_final_frame(
                    ffmpeg=ffmpeg,
                    input_frame=enhanced_frame,
                    output_frame=final_frame,
                    outscale=outscale,
                )

                # Final-frame stage occupies 80-90%.
                final_percent = int(
                    80
                    + (
                        (index + 1)
                        / total_frames
                    )
                    * 10
                )

                self._report_progress(
                    progress_callback,
                    final_percent,
                )

            # ==================================================
            # 4. REBUILD VIDEO
            # ==================================================

            print(
                "\n[4/4] Rebuilding final video..."
            )

            self._rebuild_video(
                ffmpeg=ffmpeg,
                input_path=input_path,
                enhanced_dir=final_frames_dir,
                output_path=output_path,
                fps=fps,
            )

            self._report_progress(
                progress_callback,
                100,
            )

        # ======================================================
        # COMPLETE
        # ======================================================

        print("\n" + "=" * 70)
        print("VIDEL VIDEO ENHANCEMENT COMPLETE")
        print("=" * 70)
        print(f"Saved: {output_path}")
        print("=" * 70)

        return output_path

    # ==========================================================
    # NCNN DISCOVERY
    # ==========================================================

    def _find_ncnn_executable(self):
        """
        Locate the Real-ESRGAN NCNN Vulkan executable.

        Expected project structure:

            videl/
            ├── engines/
            │   └── realesrgan-ncnn-vulkan/
            │       ├── realesrgan-ncnn-vulkan.exe
            │       ├── models/
            │       └── ...
        """

        project_root = Path(__file__).resolve().parents[2]

        executable = (
            project_root
            / "engines"
            / "realesrgan-ncnn-vulkan"
            / "realesrgan-ncnn-vulkan.exe"
        )

        if executable.exists():
            return executable

        # Fallback: relative to current working directory.
        fallback = (
            Path.cwd()
            / "engines"
            / "realesrgan-ncnn-vulkan"
            / "realesrgan-ncnn-vulkan.exe"
        )

        if fallback.exists():
            return fallback

        return None

    # ==========================================================
    # FFMPEG DISCOVERY
    # ==========================================================

    def _find_ffmpeg(self):
        """
        Locate FFmpeg through VIDEL's central discovery system.
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
        Detect the original video's frame rate using FFprobe.
        """

        ffprobe = Path(
            ffmpeg
        ).with_name("ffprobe.exe")

        if not ffprobe.exists():

            try:
                from app.services.ffmpeg_tools import ffprobe_path

                discovered_ffprobe = ffprobe_path()

                if discovered_ffprobe is not None:
                    ffprobe = Path(
                        discovered_ffprobe
                    )

            except ImportError:
                pass

        if not ffprobe.exists():
            raise RuntimeError(
                "FFprobe was not found. "
                "FFprobe is required to preserve "
                "the original video's FPS."
            )

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
        Extract the video's original frames.

        No FPS conversion is performed.
        """

        frame_pattern = (
            frames_dir
            / "frame_%08d.png"
        )

        command = [
            str(ffmpeg),

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
    # NCNN FRAME UPSCALING
    # ==========================================================

    def _upscale_frame_ncnn(
        self,
        input_frame,
        output_frame,
    ):
        """
        Run one frame through Real-ESRGAN x4plus
        using the NCNN Vulkan executable.

        The working directory is explicitly set to the
        NCNN installation directory so the executable can
        reliably find its models.
        """

        executable = self.ncnn_executable

        if executable is None:
            raise RuntimeError(
                "NCNN Vulkan executable is unavailable."
            )

        engine_dir = executable.parent

        command = [
            str(executable),

            "-i",
            str(input_frame),

            "-o",
            str(output_frame),

            "-n",
            self.AI_MODEL,

            "-s",
            str(self.AI_SCALE),

            "-g",
            "0",

            "-t",
            str(self.tile),

            "-v",
        ]

        result = subprocess.run(
            command,
            cwd=str(engine_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:

            raise RuntimeError(
                "Real-ESRGAN NCNN Vulkan failed.\n\n"
                f"Input: {input_frame}\n"
                f"Output: {output_frame}\n\n"
                f"STDOUT:\n{result.stdout}\n\n"
                f"STDERR:\n{result.stderr}"
            )

        if not output_frame.exists():

            raise RuntimeError(
                "Real-ESRGAN completed without creating "
                f"the expected output frame:\n{output_frame}"
            )

        if output_frame.stat().st_size <= 0:

            raise RuntimeError(
                "Real-ESRGAN created an empty output frame:\n"
                f"{output_frame}"
            )

    # ==========================================================
    # FINAL FRAME PREPARATION
    # ==========================================================

    def _prepare_final_frame(
        self,
        ffmpeg,
        input_frame,
        output_frame,
        outscale,
    ):
        """
        Convert the internal 4× AI result into the requested
        final output scale.

        For 2×:

            4× AI
              ↓
            Lanczos 2×
              ↓
            subtle sharpening

        This is our current Natural Quality pipeline.
        """

        # ------------------------------------------------------
        # 4× output
        # ------------------------------------------------------

        if outscale == 4:

            filter_chain = (
                "format=rgb24,"
                + self.SHARPEN_FILTER
            )

        # ------------------------------------------------------
        # 3× output
        # ------------------------------------------------------

        elif outscale == 3:

            filter_chain = (
                "scale=iw*3/4:"
                "ih*3/4:"
                "flags=lanczos+accurate_rnd,"
                + self.SHARPEN_FILTER
            )

        # ------------------------------------------------------
        # 2× output
        # ------------------------------------------------------

        elif outscale == 2:

            filter_chain = (
                "scale=iw/2:"
                "ih/2:"
                "flags=lanczos+accurate_rnd,"
                + self.SHARPEN_FILTER
            )

        # ------------------------------------------------------
        # 1× output
        # ------------------------------------------------------

        else:

            filter_chain = (
                "scale=iw/4:"
                "ih/4:"
                "flags=lanczos+accurate_rnd,"
                + self.SHARPEN_FILTER
            )

        command = [
            str(ffmpeg),

            "-y",

            "-hide_banner",

            "-loglevel",
            "error",

            "-i",
            str(input_frame),

            "-vf",
            filter_chain,

            "-frames:v",
            "1",

            "-update",
            "1",

            str(output_frame),
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
                "FFmpeg final-frame processing failed:\n"
                + result.stderr
            )

        if not output_frame.exists():

            raise RuntimeError(
                "FFmpeg did not create the final frame:\n"
                f"{output_frame}"
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
        Rebuild the final video.

        The enhanced frames use the ORIGINAL FPS.

        Original audio is copied through AAC encoding.
        """

        frame_pattern = (
            enhanced_dir
            / "frame_%08d.png"
        )

        command = [
            str(ffmpeg),

            "-y",

            "-hide_banner",

            "-loglevel",
            "error",

            # --------------------------------------------------
            # Enhanced frames
            # --------------------------------------------------

            "-framerate",
            f"{fps:.12f}",

            "-i",
            str(frame_pattern),

            # --------------------------------------------------
            # Original video/audio source
            # --------------------------------------------------

            "-i",
            str(input_path),

            # --------------------------------------------------
            # Video
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
            # Mapping
            # --------------------------------------------------

            "-map",
            "0:v:0",

            "-map",
            "1:a?",

            # --------------------------------------------------
            # Duration
            # --------------------------------------------------

            "-shortest",

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

        if not output_path.exists():

            raise RuntimeError(
                "FFmpeg finished but the output video "
                "was not created."
            )

        if output_path.stat().st_size <= 0:

            raise RuntimeError(
                "FFmpeg created an empty output video."
            )

    # ==========================================================
    # PROGRESS
    # ==========================================================

    @staticmethod
    def _report_progress(
        progress_callback,
        value,
    ):
        """
        Safely report progress.
        """

        value = max(
            0,
            min(100, int(value)),
        )

        if progress_callback:
            progress_callback(value)