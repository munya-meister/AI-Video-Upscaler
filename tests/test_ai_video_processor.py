from pathlib import Path
import time

from src.ai_engine.ai_video_processor import AIVideoProcessor


def main():

    print("=" * 60)
    print("VIDEL - AI VIDEO PROCESSOR TEST")
    print("=" * 60)

    # ----------------------------------------------------------
    # Project paths
    # ----------------------------------------------------------

    project_root = Path(__file__).resolve().parents[1]

    input_path = (
        project_root
        / "uploads"
        / "my_short_video.mp4"
    )

    output_path = (
        project_root
        / "outputs"
        / "my_short_video_test_10frames.mp4"
    )

    print(f"Input : {input_path}")
    print(f"Output: {output_path}")

    # ----------------------------------------------------------
    # Validate input
    # ----------------------------------------------------------

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input video not found:\n{input_path}"
        )

    # ----------------------------------------------------------
    # Create processor
    # ----------------------------------------------------------

    processor = AIVideoProcessor(
        tile=512
    )

    print("Tile  : 256")

    # ----------------------------------------------------------
    # Check FFmpeg
    # ----------------------------------------------------------

    ffmpeg = processor._find_ffmpeg()

    if ffmpeg is None:
        raise RuntimeError(
            "FFmpeg was not found."
        )

    print(f"FFmpeg: {ffmpeg}")

    # ----------------------------------------------------------
    # Check original FPS
    # ----------------------------------------------------------

    fps = processor._get_video_fps(
        ffmpeg,
        input_path,
    )

    print(f"Original FPS: {fps:.3f}")

    # ----------------------------------------------------------
    # Progress callback
    # ----------------------------------------------------------

    def progress(percent):

        print(
            f"Progress: {percent}%"
        )

    # ----------------------------------------------------------
    # Start timer
    # ----------------------------------------------------------

    start_time = time.time()

    print()
    print("Processing FIRST 10 FRAMES only...")
    print()

    # ----------------------------------------------------------
    # Run AI video upscaling
    # ----------------------------------------------------------

    processor.upscale_video(
        input_path=input_path,
        output_path=output_path,
        outscale=2,
        progress_callback=progress,
        max_frames=10,
    )

    # ----------------------------------------------------------
    # Calculate processing time
    # ----------------------------------------------------------

    elapsed = time.time() - start_time

    # ----------------------------------------------------------
    # Validate output
    # ----------------------------------------------------------

    if not output_path.exists():
        raise RuntimeError(
            "Output video was not created."
        )

    if output_path.stat().st_size <= 0:
        raise RuntimeError(
            "Output video is empty."
        )

    # ----------------------------------------------------------
    # Success
    # ----------------------------------------------------------

    print()
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

    print(f"Output : {output_path}")
    print(
        f"Size   : "
        f"{output_path.stat().st_size:,} bytes"
    )

    print(
        f"Time   : "
        f"{elapsed:.2f} seconds"
    )

    print(
        f"Average: "
        f"{elapsed / 10:.2f} seconds/frame"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()