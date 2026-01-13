from PIL import Image

from crimereporter.utils.scale_mode import ScaleMode


class ImageTransform:
    @staticmethod
    def scale_image(image: Image.Image, max_width: int, max_height: int) -> Image.Image:
        scale = min(max_width / image.width, max_height / image.height)
        return image.resize((int(image.width * scale), int(image.height * scale)))

    @staticmethod
    def scale_to_fit_box(image: Image.Image, w: int, h: int) -> Image.Image:
        scale = min(w / image.width, h / image.height)
        return image.resize(
            (int(image.width * scale), int(image.height * scale)),
            Image.Resampling.LANCZOS,
        )

    @staticmethod
    def scale_to_fit(image: Image.Image, max_size: int, mode: ScaleMode) -> Image.Image:
        scale = max_size / (image.width if mode == ScaleMode.WIDTH else image.height)
        return image.resize(
            (int(image.width * scale), int(image.height * scale)),
            Image.Resampling.LANCZOS,
        )
