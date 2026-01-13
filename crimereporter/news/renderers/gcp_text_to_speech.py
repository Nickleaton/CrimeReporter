import logging
import re
from io import BytesIO

from google.cloud import texttospeech
from google.cloud.texttospeech_v1 import SsmlVoiceGender
from pydub import AudioSegment

from crimereporter.news.renderers.audio import AudioRenderer
from crimereporter.utils.config import Config

logger = logging.getLogger(__name__)

config = Config()


class GCPTextToSpeechRenderer(AudioRenderer):
    """Renderer that outputs the script as a single MP3 using Google Cloud TTS."""

    renderer_name = "GCPTextToSpeech"

    def __init__(self) -> None:
        super().__init__()
        self.client = texttospeech.TextToSpeechClient.from_service_account_file(config.speech_to_text)

    def clean(self, text: str) -> str:
        phonemes = getattr(config, "phonemes", None)
        if not phonemes:
            return text

        for item in phonemes:
            phoneme_entry = item.get("phoneme")
            if not phoneme_entry:
                continue

            source = phoneme_entry.get("source")
            target = phoneme_entry.get("target")
            if not (source and target):
                continue

            # Whole word, case-insensitive pattern
            pattern = r"\b" + re.escape(source) + r"\b"

            # Replacement function—preserves original matched case
            def repl(match):
                original = match.group(0)
                # Insert original case into the target tag
                return re.sub(re.escape(source), original, target, flags=re.IGNORECASE)

            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

        if hasattr(super(), "clean"):
            return super().clean(text)
        return text

    def render_segment(self, text: str) -> AudioSegment:
        """Render a single text segment using Google Cloud TTS."""

        synthesis_input = texttospeech.SynthesisInput(ssml=f"<speak>{text}</speak>")

        voice = texttospeech.VoiceSelectionParams(
            language_code=config.audio.language_code,
            ssml_gender=SsmlVoiceGender[config.audio.voice_gender],
        )

        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )

        # Convert response bytes → AudioSegment
        with BytesIO(response.audio_content) as buf:
            return AudioSegment.from_file(buf, format="mp3")
