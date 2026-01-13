from moviepy import AudioFileClip
from moviepy.Clip import Clip

from crimereporter.news.segments.audio import AudioSegment


class TextAudioSegment(AudioSegment):
    name: str = "text"

    def load(self) -> Clip:
        audio_path = self.output_path.parent / f"segment_{self.idx:03d}.mp3"
        if not audio_path.exists():
            raise FileNotFoundError(f"TTS audio missing: {audio_path}")
        return AudioFileClip(str(audio_path))
