import logging
import tempfile
from pathlib import Path

import pyttsx3
from pydub import AudioSegment

from crimereporter.news.renderers.audio import AudioRenderer
from crimereporter.utils.config import Config

logger = logging.getLogger(__name__)

config = Config()


class PYTTSX3AudioRenderer(AudioRenderer):
    """Renderer that outputs the script as a single MP3 audio file using pyttsx3."""

    renderer_name = "PYTTSX3"

    def __init__(self):
        super().__init__()
        self.engine = pyttsx3.init()

    def render_segment(self, text: str) -> AudioSegment:
        """Render a single text segment to AudioSegment using pyttsx3."""

        lang = config.audio.language
        voices = self.engine.getProperty("voices")
        for v in voices:
            if lang in v.identifier:
                self.engine.setProperty("voice", v.identifier)
                break

        # Use a temporary WAV file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp_path = Path(tmp.name)

        try:
            # Queue TTS output
            self.engine.save_to_file(text, str(tmp_path))
            self.engine.runAndWait()

            # Load WAV into AudioSegment
            audio_segment = AudioSegment.from_file(tmp_path, format="wav")
        finally:
            tmp_path.unlink(missing_ok=True)

        return audio_segment
