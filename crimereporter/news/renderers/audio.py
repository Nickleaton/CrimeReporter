import hashlib
import logging
from pathlib import Path

from pydub import AudioSegment

from crimereporter.caches.audio_cache import AudioCache, AudioCacheRecord
from crimereporter.news.renderers.renderer import Renderer
from crimereporter.news.script import Script
from crimereporter.utils.config import Config

logger = logging.getLogger(__name__)
config = Config()

call_logger_audio = logging.getLogger("call.logger.audio")


class AudioRenderer(Renderer):
    """Base class for audio renderers with segment orchestration and caching."""

    renderer_name: str = "base"

    def __init__(self) -> None:
        self.cache = AudioCache()

    def clean(self, text: str) -> str:
        """
        Clean text prior to rendering.

        Intended for normalization, phoneme substitution, or SSML-safe escaping.
        Subclasses may override.
        """
        return text.strip()

    def render(self, script: Script, _: str, output_path: Path) -> None:
        """Render the script to a full audio file, using per-segment caching."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        full_audio = AudioSegment.silent(duration=0)

        for idx, seg in enumerate(script.segments, start=1):
            if "text" not in seg:
                continue

            text = self.clean(seg["text"])

            # Collect renderer/format info for composite key
            lang = config.audio.language
            voice = config.audio.voice
            options = config.audio.options

            # Hash the combined key
            hash_input = f"{self.renderer_name}:{lang}:{voice}:{options}:{text}"
            segment_hash = hashlib.sha256(hash_input.encode()).hexdigest()

            segment_file = output_path.parent / f"segment_{idx:03d}.mp3"

            # --- Composite message_cache lookup ---
            cached = self.cache.get(self.renderer_name, lang, voice, segment_hash)

            if cached and Path(cached.file_path).exists():
                logger.info(f"Using cached segment {idx} ({segment_hash})")
                Path(cached.file_path).replace(segment_file)
                segment_audio = AudioSegment.from_file(segment_file, format="mp3")
            else:
                try:
                    call_logger_audio.info(
                        f"{lang}, " f"{voice}, " f"{options}, " f"{len(text)}, " f"{self.renderer_name}"
                    )
                    segment_audio = self.render_segment(text)
                    segment_audio.export(segment_file)

                    # Add to message_cache using composite key
                    self.cache.add(
                        AudioCacheRecord(
                            renderer=self.renderer_name,
                            text_hash=segment_hash,
                            language=lang,
                            voice=voice,
                            file_path=str(segment_file),
                            size=len(text.split()),
                            text=text,
                        ),
                        self.renderer_name,
                        lang,
                        voice,
                        segment_hash,  # composite key parts
                    )

                    logger.info(f"Rendered segment {idx:03d} ({len(text.split())} words)")
                except Exception as e:
                    logger.error(f"Failed to render segment {idx}: {e}")
                    continue

            full_audio += segment_audio

        # Export full audio
        full_audio.export(output_path, format="mp3")
        logger.info(f"Saved AUDIO    {output_path}")

    def render_segment(self, text: str) -> AudioSegment:
        """Subclasses must implement: render a single segment to AudioSegment."""
        raise NotImplementedError
