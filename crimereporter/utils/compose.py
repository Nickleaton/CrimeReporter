from PIL import Image

from crimereporter.utils.position import Position


class ImageCompose:
    @staticmethod
    def paste_center(background: Image.Image, overlay: Image.Image, box=None) -> Image.Image:
        bg_copy = background.copy()
        if box:
            left, top, right, bottom = box
            x = left + (right - left - overlay.width) // 2
            y = top + (bottom - top - overlay.height) // 2
        else:
            x = (bg_copy.width - overlay.width) // 2
            y = (bg_copy.height - overlay.height) // 2
        bg_copy.paste(overlay, (x, y), overlay)
        return bg_copy

    @staticmethod
    def paste(base: Image.Image, overlay: Image.Image, position: Position, margin: int = 0) -> Image.Image:
        base_copy = base.copy()
        x, y = position.coordinates(base_copy, overlay, margin)
        base_copy.paste(overlay, (x, y), overlay)
        return base_copy
