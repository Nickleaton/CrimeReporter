from abc import ABC, abstractmethod
from logging import getLogger
from pathlib import Path

from crimereporter.caches.media_cache import MediaCache
from crimereporter.caches.message_cache import MessageCache

logger = getLogger(__name__)


class Poster(ABC):
    """Base class for posting messages to a platform with caching."""

    def __init__(self):
        self.message_cache = MessageCache(Path("caches") / f"{self.name}_messages.csv")
        self.media_cache = MediaCache(Path("caches") / f"{self.name}_media.csv")

    @property
    def name(self) -> str:
        return self.__class__.__name__.removesuffix("Poster")

    @abstractmethod
    def post_message(
        self,
        video_id: str,
        video_title: str,
        message: str,
        image_path: Path | None = None,
    ):
        """Post a message with optional media. Must be implemented by subclasses."""
        raise NotImplementedError

    @abstractmethod
    def upload_media(self, image_path: Path) -> str | None:
        """Upload media and return the platform-specific media ID or reference."""
        raise NotImplementedError
