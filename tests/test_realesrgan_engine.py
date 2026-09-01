import sys
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Make src importable
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_PATH))

from ai_engine.realesrgan_engine import RealESRGANEngine


def main():
    input_image = PROJECT_ROOT / "test_input.jpg"
    output_image = PROJECT_ROOT / "outputs" / "engine_test.png"

    output_image.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 55)
    print("VIDEL - Real-ESRGAN Engine Test")
    print("=" * 55)

    print(f"Input : {input_image}")
    print(f"Output: {output_image}")

    engine = RealESRGANEngine(
        tile=512,
    )

    engine.upscale_image(
        input_image,
        output_image,
        outscale=4,
    )

    print("=" * 55)
    print("ENGINE TEST SUCCESS")
    print("=" * 55)


if __name__ == "__main__":
    main()
