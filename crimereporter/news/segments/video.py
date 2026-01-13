from abc import ABC, abstractmethod

from moviepy import VideoClip

from crimereporter.news.segments.segment import Segment


class VideoSegment(Segment, ABC):
    name: str = "abstract_video"

    @abstractmethod
    def load(self) -> VideoClip:
        raise NotImplementedError
