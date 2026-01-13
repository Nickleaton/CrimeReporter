from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.Clip import Clip

from crimereporter.news.segments.audio import AudioSegment


class FileAudioSegment(AudioSegment):
    name: str = "audio"

    def load(self) -> Clip:
        audio_path = self.output_path.parent.parent / (self.segment["audio"])
        if not audio_path.exists():
            raise FileNotFoundError(f"Missing audio: {audio_path}")
        return AudioFileClip(str(audio_path))
