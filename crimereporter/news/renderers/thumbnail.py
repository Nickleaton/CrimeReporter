from pathlib import Path

from crimereporter.news.renderers.renderer import Renderer
from crimereporter.news.script import Script
from crimereporter.utils.base import ImageBase
from crimereporter.utils.config import FormatsConfig
from crimereporter.utils.image_draw import ImageDrawUtils
from crimereporter.utils.position import Position
from crimereporter.utils.scale_mode import ScaleMode


class ThumbnailRenderer(Renderer):

    def render(self, script: Script, orientation: str, output_path: Path):
        """Render a composed post image and save to disk."""
        fmt = FormatsConfig(orientation, script.parsed["Type"])
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        layers = []

        # ---------------------
        # Background
        # ---------------------
        background_image = ImageDrawUtils.background(
            fmt.thumbnail.width,
            fmt.thumbnail.height - fmt.banner.height,
            fmt.thumbnail.background_color,
        )
        layers.append((background_image, 0, 0))

        # ---------------------
        # Main image
        # ---------------------
        main_img = self.load_image(orientation, script)
        main_img = ImageBase.scale_to_fit_box(main_img, fmt.thumbnail.width, fmt.thumbnail.height - fmt.banner.height)
        x, y = ImageBase.compute_position(
            target_image=background_image,
            overlay_image=main_img,
            box=(0, 0, fmt.thumbnail.width, fmt.thumbnail.height - fmt.banner.height),
        )
        layers.append((main_img, x, y))

        # ---------------------
        # Banner
        # ---------------------
        banner_img = ImageDrawUtils.banner(script.parsed.get("Title", "Untitled"), fmt.banner)
        layers.append((banner_img, 0, y + main_img.height))

        # ---------------------
        # Flag
        # ---------------------
        flag_img = ImageDrawUtils.flag(script.type_name, fmt.flag)
        x, y = ImageBase.compute_position(
            target_image=background_image,
            overlay_image=flag_img,
            position=Position.create(fmt.flag.position),
            margin=fmt.flag.inset_margin,
        )
        layers.append((flag_img, x, y))

        # ---------------------
        # Logo
        # ---------------------
        logo_img = ImageBase.load_image(fmt.thumbnail.logo.path)
        logo_img = ImageBase.recolor_image(logo_img, fmt.thumbnail.logo.color)
        logo_img = ImageBase.scale_to_fit(logo_img, fmt.thumbnail.logo.size, ScaleMode.HEIGHT)
        x, y = ImageBase.compute_position(
            target_image=background_image,
            overlay_image=logo_img,
            position=Position.create(fmt.thumbnail.logo.position),
            margin=fmt.thumbnail.logo.margin,
        )
        layers.append((logo_img, x, y))

        composed = ImageDrawUtils.compose_layers(layers)  # uses Box.union internally

        # ---------------------
        # Save result
        # ---------------------
        composed.save(output_path, fmt="PNG")
