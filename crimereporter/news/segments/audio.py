from abc import ABC, abstractmethod

from moviepy import AudioFileClip

from crimereporter.news.segments.segment import Segment


class AudioSegment(Segment, ABC):
    name: str = "abstract_audio"

    @abstractmethod
    def load(self) -> AudioFileClip:
        raise NotImplementedError
