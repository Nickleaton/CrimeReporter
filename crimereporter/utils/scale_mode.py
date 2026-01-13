from enum import Enum


class ScaleMode(Enum):
    WIDTH = "width"
    HEIGHT = "height"

    @classmethod
    def create(cls, value: str) -> "ScaleMode":
        """
        Create a ScaleMode from a string (case-insensitive).

        Args:
            value: String representation ('width' or 'height').

        Returns:
            ScaleMode enum member.
        """
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f'Invalid ScaleMode: {value!r}. Use "width" or "height".')
