from pathlib import Path

import numpy as np
from moviepy import ImageClip
from moviepy.Clip import Clip

from crimereporter.news.segments.video import VideoSegment
from crimereporter.utils.base import ImageBase
from crimereporter.utils.image_draw import ImageDrawUtils
from crimereporter.utils.position import Position
from crimereporter.utils.scale_mode import ScaleMode


class ImageSegment(VideoSegment):
    name: str = "image"

    def load(self) -> Clip:
        """
        Create a video clip from an image segment with banner and logo.
        Returns an ImageClip without audio attached.
        """
        image_path = self.output_path.parent.parent / Path(self.segment["image"])

        layers = []
        # Background
        background_image = ImageDrawUtils.background(
            self.fmt.video.width, self.fmt.video.height, self.fmt.video.background_color
        )
        layers.append((background_image, 0, 0))

        # Main image
        main_img = ImageBase.load_image(image_path)
        main_img = ImageBase.scale_to_fit_box(
            main_img,
            self.fmt.video.width,
            self.fmt.video.height - self.fmt.banner.height,
        )
        x, y = ImageBase.compute_position(
            background_image,
            main_img,
            box=(
                0,
                0,
                self.fmt.video.width,
                self.fmt.video.height - self.fmt.banner.height,
            ),
        )
        layers.append((main_img, x, y))

        # Banner
        banner_img = ImageDrawUtils.banner(text=self.default_text, fmt=self.fmt.banner)
        layers.append((banner_img, 0, y + main_img.height))

        # Logo
        logo_img = ImageBase.load_image(self.fmt.thumbnail.logo.path)
        logo_img = ImageBase.recolor_image(logo_img, self.fmt.thumbnail.logo.color)
        logo_img = ImageBase.scale_to_fit(logo_img, self.fmt.thumbnail.logo.size, ScaleMode.HEIGHT)
        x, y = ImageBase.compute_position(
            background_image,
            logo_img,
            position=Position.create(self.fmt.thumbnail.logo.position),
            margin=self.fmt.thumbnail.logo.margin,
        )
        layers.append((logo_img, x, y))

        # Compose final image
        composed = ImageDrawUtils.compose_layers(layers).convert("RGB")  # TODO
        # Create a 1-frame clip
        clip = ImageClip(np.array(composed)).with_duration(1 / 24)
        clip = clip.without_audio()
        return clip
