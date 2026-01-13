from pathlib import Path

import numpy as np
from moviepy import CompositeVideoClip, ImageClip, VideoFileClip, vfx
from PIL import Image

from crimereporter.news.segments.video import VideoSegment
from crimereporter.utils.base import ImageBase
from crimereporter.utils.image_draw import ImageDrawUtils
from crimereporter.utils.position import Position
from crimereporter.utils.scale_mode import ScaleMode


class FileVideoSegment(VideoSegment):
    name: str = "video"

    def load(self) -> CompositeVideoClip:
        """
        Load a video segment, overlay banner and logo, and return a MoviePy VideoFileClip.
        """
        # Validate video file
        video_path = self.output_path.parent.parent / Path(self.segment["video"])
        if not video_path.exists():
            raise FileNotFoundError(f"Video file missing: {video_path}")

        # Load video
        clip = VideoFileClip(str(video_path))

        # Resize to target output dimensions
        clip = clip.with_effects([vfx.Resize(width=self.fmt.video.width, height=self.fmt.video.height)])

        # Banner overlay
        text = self.segment.get("text", self.default_text)
        if text:
            banner_img = ImageDrawUtils.banner(text=text, fmt=self.fmt.banner)
            banner_clip = ImageClip(np.array(banner_img)).with_duration(clip.duration)
            banner_clip = banner_clip.with_position(("center", "top"))
            clip = CompositeVideoClip([clip, banner_clip])

        # Logo overlay
        logo_img = ImageBase.load_image(self.fmt.thumbnail.logo.path)
        logo_img = ImageBase.recolor_image(logo_img, self.fmt.thumbnail.logo.color)
        logo_img = ImageBase.scale_to_fit(logo_img, self.fmt.thumbnail.logo.size, ScaleMode.HEIGHT)

        # Compute position using PIL Image (first frame of video)
        first_frame = Image.fromarray(clip.get_frame(0))
        x, y = ImageBase.compute_position(
            target_image=first_frame,
            overlay_image=logo_img,
            position=Position.create(self.fmt.thumbnail.logo.position),
            margin=self.fmt.thumbnail.logo.margin,
        )
        logo_clip = ImageClip(np.array(logo_img)).with_duration(clip.duration).with_position((x, y))

        # Composite video + logo
        clip = CompositeVideoClip([clip, logo_clip])

        return clip
