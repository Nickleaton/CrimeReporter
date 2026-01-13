from enum import Enum, auto
from typing import Tuple

from PIL import Image


class Position(Enum):
    TOP_LEFT = auto()
    TOP_RIGHT = auto()
    BOTTOM_LEFT = auto()
    BOTTOM_RIGHT = auto()
    LEFT = auto()
    RIGHT = auto()
    TOP = auto()
    BOTTOM = auto()
    CENTER = auto()

    @classmethod
    def create(cls, name: str) -> "Position":
        """Construct a Position from a string like 'top_left'."""
        name = name.upper().replace(" ", "_")
        if name not in cls.__members__:
            raise ValueError(f"Invalid position: {name}")
        return cls[name]

    def coordinates(self, base_img: Image.Image, overlay_img: Image.Image, margin: int = 10) -> Tuple[int, int]:
        """Get (x, y) coordinates for the overlay image.

        Args:
            base_img: PIL.Image.Image, the background image.
            overlay_img: PIL.Image.Image, the overlay image.
            margin: Margin from the edges in pixels.

        Returns:
            A tuple (x, y) with the top-left coordinates for the overlay image.
        """
        if self == Position.TOP_LEFT:
            x = margin
            y = margin
        elif self == Position.TOP_RIGHT:
            x = base_img.width - overlay_img.width - margin
            y = margin
        elif self == Position.BOTTOM_LEFT:
            x = margin
            y = base_img.height - overlay_img.height - margin
        elif self == Position.BOTTOM_RIGHT:
            x = base_img.width - overlay_img.width - margin
            y = base_img.height - overlay_img.height - margin
        elif self == Position.LEFT:
            x = margin
            y = (base_img.height - overlay_img.height) // 2
        elif self == Position.RIGHT:
            x = base_img.width - overlay_img.width - margin
            y = (base_img.height - overlay_img.height) // 2
        elif self == Position.TOP:
            x = (base_img.width - overlay_img.width) // 2
            y = margin
        elif self == Position.BOTTOM:
            x = (base_img.width - overlay_img.width) // 2
            y = base_img.height - overlay_img.height - margin
        elif self == Position.CENTER:
            x = (base_img.width - overlay_img.width) // 2
            y = (base_img.height - overlay_img.height) // 2
        else:
            # fallback to top-right
            x = base_img.width - overlay_img.width - margin
            y = margin
        return x, y
