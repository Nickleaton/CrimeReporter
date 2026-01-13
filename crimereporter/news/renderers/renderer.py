import logging
from abc import ABC, abstractmethod
from pathlib import Path

from PIL import Image
from pydub import AudioSegment

from crimereporter.news.script import Script
from crimereporter.utils.base import ImageBase
from crimereporter.utils.config import FormatsConfig
from crimereporter.utils.image_draw import ImageDrawUtils

logger = logging.getLogger(__name__)


class Renderer(ABC):
    """Abstract base class for different renderers.

    Subclasses must implement the `render` method.
    """

    @abstractmethod
    def render(self, script: Script, orientation: str, output_path: Path) -> None:
        """Render the script to a specific fmt."""
        pass

    @staticmethod
    def load_image(orientation: str, script: Script) -> Image.Image:
        """Load and scale the thumbnail image while preserving aspect ratio."""
        fmt = FormatsConfig(orientation, script.parsed["Type"])
        filename = script.directory / script.parsed["Thumbnail"]
        if not Path(filename).exists():
            filename = Path("files") / Path(filename).name
        if not Path(filename).exists():
            raise FileNotFoundError(f"Thumbnail file not found: {Path(filename).name}")

        image = Image.open(filename).convert("RGBA")

        # Scale while preserving aspect ratio
        scale = min(fmt.video.width / image.width, fmt.video.height / image.height)
        new_width = round(image.width * scale)
        new_height = round(image.height * scale)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return image

    @staticmethod
    def get_logo(orientation: str, script: Script) -> Image.Image | None:
        fmt = FormatsConfig(orientation, script.parsed["Type"])
        logo_path = fmt.thumbnail.logo.path
        if not logo_path:
            return None

        logo_path = Path(logo_path)
        if not logo_path.exists():
            logger.warning(f"Logo file '{logo_path}' not found. Skipping logo overlay.")
            return None

        logger.info(f"Loading logo from {logo_path}")

        # Load logo without scaling
        logo = ImageBase.load_image(str(logo_path))

        if fmt.thumbnail.logo.color:
            logo = ImageDrawUtils.recolor_image(logo, fmt.thumbnail.logo.color)

        return logo

    @staticmethod
    def merge_audio(script: Script, output_path: Path):
        # Export final audio
        """Read all segment MP3 files and concatenate into a single file."""
        full_audio = AudioSegment.silent(duration=0)

        for idx, seg in enumerate(script.segments, start=1):
            segment_file = output_path.parent / f"segment_{idx:03d}.mp3"
            if not segment_file.exists():
                logger.warning(f"Segment file {segment_file} does not exist, skipping.")
                continue

            audio_segment = AudioSegment.from_file(segment_file, format="mp3")
            full_audio += audio_segment

        # Export combined audio
        final_file = output_path.parent / "audio.mp3"
        full_audio.export(final_file, format="mp3")
        logger.info(f"Saved AUDIO    {final_file}")
