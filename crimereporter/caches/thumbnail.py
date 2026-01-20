from dataclasses import dataclass
from pathlib import Path

from crimereporter.caches.cache import BaseCache
from crimereporter.utils.config import Config

config = Config()


@dataclass
class ThumbnailCacheRecord:
    thumbnail_hash: str
    video_id: str


class ThumbnailCache(BaseCache[ThumbnailCacheRecord]):

    def __init__(self, cache_file: Path = Path(config.root) / "caches/youtube_thumbnail.csv"):
        super().__init__(csv_file=cache_file, record_cls=ThumbnailCacheRecord, key_field="video_id")
