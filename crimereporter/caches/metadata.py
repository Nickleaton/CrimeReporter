from dataclasses import dataclass
from pathlib import Path

from crimereporter.caches.cache import BaseCache
from crimereporter.utils.config import Config

config = Config()


@dataclass
class MetadataCacheRecord:
    video_id: str
    metadata_hash: str


class MetadataCache(BaseCache[MetadataCacheRecord]):
    def __init__(self, cache_file: Path = Path(config.root) / "caches/youtube_metadata.csv"):
        super().__init__(csv_file=cache_file, record_cls=MetadataCacheRecord, key_field="video_id")
