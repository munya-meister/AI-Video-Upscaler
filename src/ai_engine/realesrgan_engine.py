from pathlib import Path

import cv2
import torch
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer


class RealESRGANEngine:
    def __init__(
        self,
        model_path=None,
        scale=4,
        tile=512,
        tile_pad=10,
        pre_pad=0,
        half=False,
    ):
        project_root = Path(__file__).resolve().parents[2]

        if model_path is None:
            model_path = project_root / "weights" / "RealESRGAN_x4plus.pth"

        model_path = Path(model_path)

        if not model_path.exists():
            raise FileNotFoundError(
                f"Real-ESRGAN weights not found: {model_path}"
            )

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.scale = scale
        self.tile = tile

        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=4,
        )

        self.upsampler = RealESRGANer(
            scale=scale,
            model_path=str(model_path),
            model=model,
            tile=tile,
            tile_pad=tile_pad,
            pre_pad=pre_pad,
            half=half and self.device.type == "cuda",
        )

        print(f"Model: RealESRGAN_x4plus")
        print(f"Weights: LOADED")
        print(f"Device: {self.device.type.upper()}")

    def upscale_image(
        self,
        input_path,
        output_path,
        outscale=4,
    ):
        input_path = Path(input_path)
        output_path = Path(output_path)

        if not input_path.exists():
            raise FileNotFoundError(
                f"Input image not found: {input_path}"
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        image = cv2.imread(str(input_path), cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError(
                f"Could not read image: {input_path}"
            )

        output, _ = self.upsampler.enhance(
            image,
            outscale=outscale,
        )

        success = cv2.imwrite(
            str(output_path),
            output,
        )

        if not success:
            raise IOError(
                f"Failed to save output image: {output_path}"
            )

        print(f"Input : {input_path}")
        print(f"Output: {output_path}")
        print("Upscaling complete.")

        return output_path