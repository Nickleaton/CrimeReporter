import logging
from pathlib import Path

from pydub import AudioSegment

logger = logging.getLogger(__name__)


class AudioMerger:
    """Utility class for concatenating audio segments into a single MP3 file."""

    @staticmethod
    def merge(script, output_path: Path) -> Path:
        """Concatenate all segment MP3 files for the given script.

        Args:
            script: Script instance containing segment information.
            output_path: Path to where the final audio should be saved.

        Returns:
            Path to the merged audio file.
        """
        full_audio = AudioSegment.silent(duration=0)

        for idx, _ in enumerate(script.segments, start=1):
            segment_file = output_path.parent / f"segment_{idx:03d}.mp3"
            if not segment_file.exists():
                logger.warning(f"Segment file {segment_file} does not exist, skipping.")
                continue

            audio_segment = AudioSegment.from_file(segment_file, format="mp3")
            full_audio += audio_segment

        final_file = output_path.parent / "audio.mp3"
        full_audio.export(final_file, format="mp3")
        logger.info(f"Saved AUDIO {final_file}")

        return final_file
