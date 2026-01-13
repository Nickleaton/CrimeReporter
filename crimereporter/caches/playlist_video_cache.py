from dataclasses import dataclass
from pathlib import Path

from crimereporter.caches.cache import BaseCache


@dataclass
class PlaylistVideoCacheRecord:
    list: str
    title: str


class PlaylistVideoCache(BaseCache[PlaylistVideoCacheRecord]):

    def __init__(self, cache_file: Path):
        super().__init__(csv_file=cache_file, record_cls=PlaylistVideoCacheRecord, key_field="key")
