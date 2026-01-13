from dataclasses import dataclass
from pathlib import Path

from crimereporter.caches.cache import BaseCache


@dataclass
class MediaCacheRecord:
    filename: str
    media_id: str


class MediaCache(BaseCache[MediaCacheRecord]):

    def __init__(self, cache_file: Path):
        super().__init__(csv_file=cache_file, record_cls=MediaCacheRecord, key_field="filename")
