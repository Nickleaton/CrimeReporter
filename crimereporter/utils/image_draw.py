from PIL import Image, ImageColor, ImageDraw

from crimereporter.utils.align import TextAlign
from crimereporter.utils.base import ImageBase
from crimereporter.utils.box import Box


class ImageDrawUtils:
    """Utility class for creating text-based RGBA files."""

    @staticmethod
    def text_image(text: str, fmt) -> Image.Image:
        """Render a generic text-based RGBA image according to fmt configuration.

        Args:
            text (str): Text string to render.
            fmt: Format configuration object defining attributes such as
                width, height, font, text color, outline color, and alignment.

        Returns:
            Image.Image: An RGBA image containing the rendered text.
        """
        # Normalize colors and load font
        bg_color = ImageBase.normalize_color(fmt.background)
        text_color = ImageBase.normalize_color(fmt.text_color)
        outline_color = ImageBase.normalize_color(fmt.outline_color)

        font = ImageBase.font(fmt.font_path, fmt.font_size)
        align = TextAlign.create(fmt.alignment)

        img = Image.new("RGBA", (fmt.width, fmt.height), bg_color)
        draw = ImageDraw.Draw(img)

        # Calculate text placement
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = int(bbox[2] - bbox[0])
        text_h = int(bbox[3] - bbox[1])
        x = align.compute_x(fmt.width, text_w, fmt.text_margin)
        y = (fmt.height - text_h) / 2 - bbox[1]

        # Draw text with optional outline
        draw.text(
            (x, y),
            text,
            font=font,
            fill=text_color,
            stroke_width=fmt.outline_width,
            stroke_fill=outline_color,
        )

        return img

    @staticmethod
    def banner(text: str, fmt) -> Image.Image:
        """Render a banner text image.

        Args:
            text (str): Banner text to render.
            fmt: Format configuration object for the banner.

        Returns:
            Image.Image: An RGBA image containing the banner text.
        """
        return ImageDrawUtils.text_image(text, fmt)

    @staticmethod
    def flag(text: str, fmt) -> Image.Image:
        """Render a flag text image.

        Args:
            text (str): Flag text to render.
            fmt: Format configuration object for the flag.

        Returns:
            Image.Image: An RGBA image containing the flag text.
        """
        return ImageDrawUtils.text_image(text, fmt)

    @staticmethod
    def background(width: int, height: int, color: str) -> Image.Image:
        """Create a solid RGBA background image.

        Args:
            width: Width of the background in pixels.
            height: Height of the background in pixels.
            color: Background color as a name (e.g., 'red') or hex string (e.g., '#FF0000').

        Returns:
            Image.Image: A new RGBA image filled with the specified color.
        """
        color = ImageBase.normalize_color(color)
        return Image.new("RGBA", (width, height), color)

    @staticmethod
    def recolor_image(image: Image.Image, color: str) -> Image.Image:
        """
        Recolor an RGBA image using a solid tint color.
        `color` is a hex string like "#FF0000".
        """
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # Create a solid color image
        r, g, b = ImageColor.getrgb(color)
        solid = Image.new("RGBA", image.size, (r, g, b, 255))

        # Combine solid color with alpha from original
        alpha = image.split()[-1]
        solid.putalpha(alpha)

        return solid

    @staticmethod
    def compose_layers(layers: list[tuple[Image.Image, int, int]]) -> Image.Image:
        """
        Composite a list of layers onto a dynamically sized canvas.

        Args:
            layers: List of tuples (image, x, y) to paste onto the canvas.

        Returns:
            A new PIL.Image with all layers composited.
        """
        if not layers:
            raise ValueError("No layers provided for compositing")

        # Step 1: Create Box objects for all layers
        boxes = [Box(x, y, img.width, img.height) for img, x, y in layers]

        # Step 2: Compute the union of all boxes to determine canvas size
        bounds = Box.union(boxes)

        # Step 3: Create base canvas of the exact required size
        base_canvas = ImageDrawUtils.background(bounds.width, bounds.height, "green")

        # Step 4: Paste each layer onto the canvas
        canvas_copy = base_canvas.copy()
        for img, x, y in layers:
            canvas_copy.paste(img, (x, y), mask=img)  # respects transparency

        return canvas_copy
