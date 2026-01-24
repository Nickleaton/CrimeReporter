from dataclasses import dataclass
from pathlib import Path

from crimereporter.caches.csv_cache import CSVCache


@dataclass
class MessageCacheRecord:
    video_id: str
    video_title: str
    message: str


class MessageCache(CSVCache[MessageCacheRecord]):
    def __init__(self, cache_file: Path):
        super().__init__(
            csv_file=cache_file, record_cls=MessageCacheRecord, key_field="video_id"
        )
