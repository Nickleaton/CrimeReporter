from dataclasses import dataclass
from pathlib import Path

from crimereporter.caches.cache import BaseCache


@dataclass
class PlaylistCacheRecord:
    name: str
    id: str


class PlaylistCache(BaseCache[PlaylistCacheRecord]):

    def __init__(self, cache_file: Path):
        super().__init__(csv_file=cache_file, record_cls=PlaylistCacheRecord, key_field="name")
