from dataclasses import dataclass


@dataclass
class Box:
    x: int = 0  # Left position
    y: int = 0  # Top position
    width: int = 0
    height: int = 0

    @property
    def left(self) -> int:
        return self.x

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def top(self) -> int:
        return self.y

    @property
    def bottom(self) -> int:
        return self.y + self.height

    def bounding_box(self) -> tuple[int, int, int, int]:
        """Return (left, top, right, bottom)."""
        return self.left, self.top, self.right, self.bottom

    def move_to(self, x: int, y: int):
        """Move the box to a new position."""
        self.x = x
        self.y = y

    def center_inside(self, container: "Box"):
        """Center this box inside another box."""
        self.x = container.x + (container.width - self.width) // 2
        self.y = container.y + (container.height - self.height) // 2

    @staticmethod
    def union(boxes: list["Box"]) -> "Box":
        """Return a Box that fully contains all given boxes."""
        if not boxes:
            return Box()
        min_left = min(box.left for box in boxes)
        min_top = min(box.top for box in boxes)
        max_right = max(box.right for box in boxes)
        max_bottom = max(box.bottom for box in boxes)
        return Box(
            x=min_left,
            y=min_top,
            width=max_right - min_left,
            height=max_bottom - min_top,
        )
