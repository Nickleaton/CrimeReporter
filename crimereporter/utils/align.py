from enum import Enum


class TextAlign(Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"

    @classmethod
    def create(cls, name: str) -> "TextAlign":
        """Create a TextAlign from a string name (case-insensitive)."""
        try:
            return cls(name.lower())
        except ValueError as e:
            raise ValueError(f"Invalid alignment name: {name!r}") from e

    def compute_x(self, width: int, text_width: int, margin: int = 0) -> int:
        """Compute the x-coordinate for the given alignment.

        Args:
            width (int): Total available width.
            text_width (int): Width of the text to align.
            margin (int): Margin to apply for left or right alignment.

        Returns:
            int: The x-coordinate for the aligned text.

        Raises:
            ValueError: If the alignment is unsupported.
        """
        if self is TextAlign.CENTER:
            return (width - text_width) // 2
        elif self is TextAlign.RIGHT:
            return width - text_width - margin
        elif self is TextAlign.LEFT:
            return margin
        else:
            raise ValueError(f"Unsupported alignment mode: {self}")
