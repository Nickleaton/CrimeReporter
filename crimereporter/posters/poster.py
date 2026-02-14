from abc import ABC, abstractmethod
from logging import getLogger
from pathlib import Path

from crimereporter.caches.media_cache import MediaCache
from crimereporter.caches.message_cache import MessageCache
from crimereporter.utils.config import Config

logger = getLogger(__name__)
config = Config()


class Poster(ABC):
    """Base class for posting messages to a platform with caching."""

    def __init__(self):
        self.message_cache = MessageCache(
            Path(config.root) / f"caches/{self.name}_messages.csv"
        )
        self.media_cache = MediaCache(
            Path(config.root) / f"caches/{self.name}_media.csv"
        )

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
