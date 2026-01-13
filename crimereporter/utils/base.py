from io import BytesIO
from pathlib import Path

import cairosvg
from PIL import Image, ImageFont
from webcolors import name_to_rgb

from crimereporter.utils.position import Position
from crimereporter.utils.scale_mode import ScaleMode


class ImageBase:
    @staticmethod
    def normalize_color(color):
        if color is None:
            return None
        return name_to_rgb(color.lower()) if isinstance(color, str) else color

    @staticmethod
    def font(path: str, size: int = 80) -> ImageFont.FreeTypeFont:
        try:
            return ImageFont.truetype(path or "arial.ttf", size)
        except OSError:
            return ImageFont.load_default()

    @staticmethod
    def load_image(filename: str | Path) -> Image.Image:
        path = Path(filename)
        if not path.exists():
            path = Path("images") / path.name
        if not path.exists():
            raise FileNotFoundError(filename)
        if path.suffix.lower() == ".svg":
            with BytesIO() as buf:
                cairosvg.svg2png(url=str(path), write_to=buf)
                buf.seek(0)
                return Image.open(buf).convert("RGBA")
        return Image.open(path).convert("RGBA")

    @staticmethod
    def recolor_image(img: Image.Image, color: str) -> Image.Image:
        """
        Recolor an image using a named color or hex string while preserving alpha.

        Args:
            img: The source RGBA image.
            color: Color to apply (name string like "red" or hex string like "#FF0000").

        Returns:
            A new PIL Image with the recolor applied.
        """
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        rgb_color = ImageBase.normalize_color(color)
        rgba_color = (*rgb_color, 255)

        r, g, b, a = img.split()
        color_img = Image.new("RGBA", img.size, rgba_color)
        recolored = Image.composite(color_img, img, a)
        return recolored

    @staticmethod
    def scale_to_fit(image: Image.Image, max_size: int, mode: ScaleMode) -> Image.Image:
        """
        Scale an image to fit within a given width or height, preserving aspect ratio.

        Args:
            image: PIL Image to scale.
            max_size: Maximum size in pixels (applies to width or height depending on mode).
            mode: ScaleMode enum indicating whether to constrain by width or height.

        Returns:
            A new scaled PIL Image.
        """
        if mode == ScaleMode.WIDTH:
            scale = max_size / image.width
        elif mode == ScaleMode.HEIGHT:
            scale = max_size / image.height
        else:
            raise ValueError(f"Unsupported scale mode: {mode}")

        new_width = max(1, round(image.width * scale))
        new_height = max(1, round(image.height * scale))
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    @staticmethod
    def resize_for_upload(file_path: Path, max_bytes: int, poster_name: str) -> Path:
        if file_path.stat().st_size <= max_bytes:
            return file_path

        img = Image.open(file_path).convert("RGBA")
        width, height = img.size

        new_name = f"{file_path.stem}_{poster_name.lower()}{file_path.suffix}"
        new_path = file_path.parent / new_name

        while True:
            buffer = BytesIO()
            img.save(buffer, format=img.format or "PNG")
            current_size = buffer.tell()
            if current_size <= max_bytes:
                new_path.write_bytes(buffer.getvalue())
                return new_path

            scale_factor = (max_bytes / current_size) ** 0.5
            width = max(1, int(width * scale_factor))
            height = max(1, int(height * scale_factor))
            img = img.resize((width, height), Image.Resampling.LANCZOS)

    @staticmethod
    def scale_to_fit_box(image: Image.Image, box_width: int, box_height: int) -> Image.Image:
        """Scale image to fit within a bounding box, preserving aspect ratio."""
        scale = min(box_width / image.width, box_height / image.height)
        new_width = int(image.width * scale)
        new_height = int(image.height * scale)
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    @staticmethod
    def compute_position(
        target_image: Image.Image,
        overlay_image: Image.Image,
        position: Position = Position.CENTER,
        margin: int = 0,
        box: tuple[int, int, int, int] | None = None,
    ) -> tuple[int, int]:
        """
        Compute coordinates to place an overlay on a target image.
        Can optionally center inside a bounding box.

        Args:
            target_image: Background image.
            overlay_image: Image to place.
            position: Position enum specifying placement.
            margin: Pixels to offset from edges (ignored for CENTER).
            box: Optional (left, top, right, bottom) bounding box.

        Returns:
            Tuple[int, int]: Coordinates (x, y) to place overlay.
        """
        if box:
            left, top, right, bottom = box
            box_width = right - left
            box_height = bottom - top
            x = left + (box_width - overlay_image.width) // 2
            y = top + (box_height - overlay_image.height) // 2
        else:
            x, y = position.coordinates(target_image, overlay_image, margin)

        return int(x), int(y)

    @staticmethod
    def paste_image_center(
        background: Image.Image,
        overlay: Image.Image,
        box: tuple[int, int, int, int] | None = None,
    ) -> Image.Image:
        """Paste overlay centered inside a bounding box or full background."""
        bg_copy = background.copy()
        x, y = ImageBase.compute_position(bg_copy, overlay, box=box)
        mask = overlay if overlay.mode in ("RGBA", "LA") else None
        bg_copy.paste(overlay, (x, y), mask)
        return bg_copy

    @staticmethod
    def paste(
        target_image: Image.Image,
        overlay_image: Image.Image,
        position: Position,
        margin: int = 0,
    ) -> Image.Image:
        """
        Return a new image with an overlay pasted at a specified position and margin.
        The original target_image is not modified.

        Args:
            target_image: Background image.
            overlay_image: Image to paste.
            position: Position enum specifying placement.
            margin: Pixels to offset from edges (ignored for CENTER).

        Returns:
            A new PIL.Image with overlay pasted.
        """
        result_image = target_image.copy()
        x, y = ImageBase.compute_position(result_image, overlay_image, position, margin)
        mask = overlay_image if overlay_image.mode in ("RGBA", "LA") else None
        result_image.paste(overlay_image, (x, y), mask)
        return result_image
