from io import BytesIO

from gtts import gTTS
from pydub import AudioSegment

from crimereporter.news.renderers.audio import AudioRenderer
from crimereporter.utils.config import Config

config = Config()


class GTTSAudioRenderer(AudioRenderer):
    """Renderer that outputs the script as a single MP3 audio file using gTTS."""

    renderer_name = "GTTS"

    def render_segment(self, text: str) -> AudioSegment:
        with BytesIO() as buf:
            tts = gTTS(text=text, lang=config.audio.language)
            tts.write_to_fp(buf)
            buf.seek(0)
            return AudioSegment.from_file(buf, format="mp3")
