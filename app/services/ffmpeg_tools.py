import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from app.models.project import VideoMetadata

# ==========================================================
# PATHS
# ==========================================================

APP_ROOT = Path(__file__).resolve().parents[2]

# These are the locations VIDEL will check for FFmpeg.
TOOL_DIRECTORIES = [
    APP_ROOT / "bin",
    APP_ROOT / "tools",
    APP_ROOT / "ffmpeg",
    APP_ROOT / "ffmpeg" / "bin",
    APP_ROOT / "tools" / "ffmpeg",
    APP_ROOT / "tools" / "ffmpeg" / "bin",
]


# ==========================================================
# WINDOWS PROCESS SETTINGS
# ==========================================================


def _hidden_kwargs() -> dict:
    kwargs = {}

    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    return kwargs


# ==========================================================
# TOOL DISCOVERY
# ==========================================================


def find_tool(name: str) -> Optional[str]:
    """
    Find an FFmpeg executable.

    Search order:
    1. Project bundled locations
    2. Common Windows installation locations
    3. System PATH

    On Windows, .exe is automatically checked.
    """

    executable_names = [name]

    if os.name == "nt" and not name.lower().endswith(".exe"):
        executable_names.append(f"{name}.exe")

    # ------------------------------------------------------
    # 1. Project bundled locations
    # ------------------------------------------------------

    for directory in TOOL_DIRECTORIES:
        if not directory.exists():
            continue

        for executable_name in executable_names:
            candidate = directory / executable_name

            if candidate.is_file():
                return str(candidate.resolve())

    # ------------------------------------------------------
    # 2. Common Windows FFmpeg locations
    # ------------------------------------------------------

    if os.name == "nt":
        common_directories = [
            Path(r"C:\ffmpeg\bin"),
            Path(r"C:\Program Files\ffmpeg\bin"),
            Path(r"C:\Program Files (x86)\ffmpeg\bin"),
            Path(os.environ.get("LOCALAPPDATA", "")) / "ffmpeg" / "bin",
            Path(os.environ.get("USERPROFILE", "")) / "ffmpeg" / "bin",
        ]

        for directory in common_directories:
            if not directory.exists():
                continue

            for executable_name in executable_names:
                candidate = directory / executable_name

                if candidate.is_file():
                    return str(candidate.resolve())

    # ------------------------------------------------------
    # 3. System PATH
    # ------------------------------------------------------

    for executable_name in executable_names:
        try:
            found = shutil.which(executable_name)

            if found:
                return str(Path(found).resolve())

        except Exception:
            pass

    return None


# ==========================================================
# AVAILABILITY
# ==========================================================


def ffmpeg_path() -> Optional[str]:
    return find_tool("ffmpeg")


def ffprobe_path() -> Optional[str]:
    return find_tool("ffprobe")


def ffmpeg_available() -> bool:
    return ffmpeg_path() is not None


def ffprobe_available() -> bool:
    return ffprobe_path() is not None


# ==========================================================
# STATUS
# ==========================================================


def ffmpeg_status_text() -> str:

    path = ffmpeg_path()

    if path:
        return "FFmpeg: Available"

    return "FFmpeg: Not Found"


def ffprobe_status_text() -> str:

    path = ffprobe_path()

    if path:
        return "FFprobe: Available"

    return "FFprobe: Not Found"


# ==========================================================
# FRAME RATE
# ==========================================================


def _parse_frame_rate(value) -> Optional[float]:

    if not value:
        return None

    try:

        text = str(value)

        if "/" in text:

            num, den = text.split("/", 1)

            den_f = float(den)

            if den_f == 0:
                return None

            return float(num) / den_f

        return float(text)

    except (TypeError, ValueError, ZeroDivisionError):

        return None


# ==========================================================
# VIDEO PROBING
# ==========================================================


def probe_video(file_path: str) -> VideoMetadata:
    """
    Inspect a video using FFprobe.

    FFprobe is preferred.

    OpenCV is used as a fallback for basic
    video information if FFprobe is unavailable.
    """

    metadata = VideoMetadata()

    path = Path(file_path)

    # ------------------------------------------------------
    # File size
    # ------------------------------------------------------

    try:

        metadata.file_size = path.stat().st_size

    except OSError:

        pass

    probe = ffprobe_path()

    # ------------------------------------------------------
    # FFprobe unavailable
    # ------------------------------------------------------

    if probe is None:

        _fill_cv2(path, metadata)

        _finalize_resolution(metadata)

        return metadata

    # ------------------------------------------------------
    # Run FFprobe
    # ------------------------------------------------------

    try:

        result = subprocess.run(
            [
                probe,
                "-v",
                "error",
                "-show_format",
                "-show_streams",
                "-print_format",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
            **_hidden_kwargs(),
        )

        if result.returncode != 0 or not result.stdout:

            _fill_cv2(path, metadata)

            _finalize_resolution(metadata)

            return metadata

        data = json.loads(result.stdout)

        # --------------------------------------------------
        # Container / format
        # --------------------------------------------------

        fmt = data.get("format") or {}

        if fmt.get("format_name"):

            metadata.container = str(fmt["format_name"])

        if fmt.get("duration"):

            try:

                metadata.duration = float(fmt["duration"])

            except (TypeError, ValueError):

                pass

        if fmt.get("size") and metadata.file_size is None:

            try:

                metadata.file_size = int(fmt["size"])

            except (TypeError, ValueError):

                pass

        # --------------------------------------------------
        # Streams
        # --------------------------------------------------

        for stream in data.get("streams") or []:

            codec_type = stream.get("codec_type")

            # ----------------------------------------------
            # Video
            # ----------------------------------------------

            if codec_type == "video" and metadata.video_codec is None:

                if stream.get("width"):

                    metadata.width = int(stream["width"])

                if stream.get("height"):

                    metadata.height = int(stream["height"])

                if stream.get("codec_name"):

                    metadata.video_codec = str(stream["codec_name"])

                    metadata.codec = metadata.video_codec

                if stream.get("duration") and metadata.duration is None:

                    try:

                        metadata.duration = float(stream["duration"])

                    except (TypeError, ValueError):

                        pass

                metadata.frame_rate = _parse_frame_rate(
                    stream.get("r_frame_rate") or stream.get("avg_frame_rate")
                )

            # ----------------------------------------------
            # Audio
            # ----------------------------------------------

            elif codec_type == "audio" and metadata.audio_codec is None:

                if stream.get("codec_name"):

                    metadata.audio_codec = str(stream["codec_name"])

    except Exception:

        _fill_cv2(path, metadata)

    # ------------------------------------------------------
    # OpenCV fallback for dimensions
    # ------------------------------------------------------

    if metadata.width is None or metadata.height is None:

        _fill_cv2(path, metadata)

    _finalize_resolution(metadata)

    return metadata


# ==========================================================
# RESOLUTION
# ==========================================================


def _finalize_resolution(
    metadata: VideoMetadata,
) -> None:

    if metadata.width and metadata.height:

        metadata.resolution = f"{metadata.width}x{metadata.height}"


# ==========================================================
# OPENCV FALLBACK
# ==========================================================


def _fill_cv2(
    path: Path,
    metadata: VideoMetadata,
) -> None:

    try:

        import cv2

        cap = cv2.VideoCapture(str(path))

        if not cap.isOpened():

            return

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)

        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

        fps = cap.get(cv2.CAP_PROP_FPS) or 0

        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0

        cap.release()

        if width and metadata.width is None:

            metadata.width = width

        if height and metadata.height is None:

            metadata.height = height

        if fps > 0 and metadata.frame_rate is None:

            metadata.frame_rate = float(fps)

        if fps > 0 and frame_count > 0 and metadata.duration is None:

            metadata.duration = float(frame_count / fps)

    except Exception:

        return


# ==========================================================
# OUTPUT VALIDATION
# ==========================================================


def output_is_valid(
    output_path: str,
) -> bool:

    path = Path(output_path)

    try:

        return path.is_file() and path.stat().st_size > 0

    except OSError:

        return False
