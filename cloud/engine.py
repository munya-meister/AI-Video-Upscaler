"""GPU-hosted Real-ESRGAN NCNN Vulkan video pipeline; no Python torch dependency."""
from __future__ import annotations
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

FFMPEG = os.getenv("VIDEL_FFMPEG", "ffmpeg")
FFPROBE = os.getenv("VIDEL_FFPROBE", "ffprobe")
NCNN = os.getenv("VIDEL_REALESRGAN", "/opt/realesrgan/realesrgan-ncnn-vulkan")
MODELS = os.getenv("VIDEL_MODEL_DIR", "/opt/realesrgan/models")
TILE = int(os.getenv("VIDEL_TILE", "128"))

def run(args: list[str], timeout: int) -> None:
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or "Video command failed")[-2000:])

def probe(path: Path) -> dict:
    result = subprocess.run(
        [FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,avg_frame_rate:format=duration", "-of", "json", str(path)],
        capture_output=True, text=True, timeout=30, check=True,
    )
    obj = json.loads(result.stdout)
    stream = (obj.get("streams") or [None])[0]
    if not stream:
        raise ValueError("No video stream found")
    w, h = int(stream["width"]), int(stream["height"])
    duration = float(obj.get("format", {}).get("duration") or 0)
    rate = stream.get("avg_frame_rate", "0/1")
    num, den = (rate.split("/") + ["1"])[:2] if "/" in rate else (rate, "1")
    fps = float(num) / float(den) if float(den) else 0
    if w <= 0 or h <= 0 or duration <= 0 or fps <= 0:
        raise ValueError("Unsupported video metadata")
    return {"width": w, "height": h, "duration": duration, "fps": fps}

def enhance(source: Path, target: Path, scale: int, quality: str,
            progress: Callable[[int], None]) -> None:
    if scale not in (2, 4):
        raise ValueError("Supported scales: 2x or 4x")
    crf = {"Standard": 23, "High Quality": 18, "Maximum Quality": 15}[quality]
    with tempfile.TemporaryDirectory(prefix="videl-", dir=str(source.parent)) as scratch:
        root = Path(scratch)
        inp, out = root / "frames", root / "enhanced"
        inp.mkdir(); out.mkdir()
        progress(5)
        run([FFMPEG, "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(source), "-vsync", "0", str(inp / "frame_%08d.png")], 1800)
        frames = sorted(inp.glob("frame_*.png"))
        if not frames:
            raise RuntimeError("No frames extracted")
        progress(12)
        # Per-frame invocation is slower but avoids the directory-mode hang seen on
        # some Vulkan drivers. A future worker can add tested batching.
        for index, frame in enumerate(frames, 1):
            enhanced = out / frame.name
            run([NCNN, "-i", str(frame), "-o", str(enhanced), "-n",
                 "realesrgan-x4plus", "-m", MODELS, "-s", str(scale),
                 "-t", str(TILE), "-j", "1:1:1", "-f", "png"], 600)
            if not enhanced.is_file():
                raise RuntimeError("Enhancement engine did not create output frame")
            progress(12 + int(76 * index / len(frames)))
        progress(90)
        run([FFMPEG, "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
             "-framerate", f"{probe(source)['fps']:.06f}",
             "-i", str(out / "frame_%08d.png"), "-i", str(source),
             "-map", "0:v:0", "-map", "1:a?", "-c:v", "libx264",
             "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
             str(target)], 1800)
        if not target.is_file() or target.stat().st_size == 0:
            raise RuntimeError("Output video missing")
        progress(100)
