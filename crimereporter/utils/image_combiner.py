from pathlib import Path
from typing import Sequence

from PIL import Image

from crimereporter.utils.base import ImageBase


class ImageCombiner:
    """Combine multiple files into a single image grid."""

    def __init__(self, image_paths: Sequence[str | Path], layout: tuple[int, int]):
        """
        Initialize the combiner.

        Args:
            image_paths: List of paths to image files.
            layout: Tuple (cols, rows) defining how files are arranged.
                    For example, (2, 1) places files side by side.
        """
        self.image_paths = [Path(p) for p in image_paths]
        self.cols, self.rows = layout

        expected_count = self.cols * self.rows
        if len(self.image_paths) != expected_count:
            raise ValueError(f"Expected {expected_count} files for layout {layout}, got {len(self.image_paths)}.")

    def load_images(self) -> list[Image.Image]:
        """Load all files into memory."""
        return [ImageBase.load_image(path) for path in self.image_paths]

    def scale_images(self, images: list[Image.Image]) -> list[Image.Image]:
        """Scale files so that all share the largest width and height."""
        max_width = max(img.width for img in images)
        max_height = max(img.height for img in images)

        scaled = []
        for img in images:
            if img.width != max_width or img.height != max_height:
                scale = max(max_width / img.width, max_height / img.height)
                new_size = (int(img.width * scale), int(img.height * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

                # Center crop to target size
                left = (img.width - max_width) // 2
                top = (img.height - max_height) // 2
                img = img.crop((left, top, left + max_width, top + max_height))
            scaled.append(img)

        return scaled

    def combine(self) -> Image.Image:
        """
        Combine all files into one composite image according to the layout.

        Returns:
            A new PIL Image arranged in the specified grid.
        """
        images = self.load_images()
        scaled = self.scale_images(images)

        max_width = max(img.width for img in scaled)
        max_height = max(img.height for img in scaled)
        total_width = self.cols * max_width
        total_height = self.rows * max_height

        combined = Image.new("RGBA", (total_width, total_height), (255, 255, 255, 0))

        for idx, img in enumerate(scaled):
            col = idx % self.cols
            row = idx // self.cols
            x = col * max_width
            y = row * max_height
            combined.paste(img, (x, y), img)

        return combined
