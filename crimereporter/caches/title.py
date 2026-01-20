from dataclasses import dataclass
from pathlib import Path

from crimereporter.caches.cache import BaseCache
from crimereporter.utils.config import Config

config = Config()


@dataclass
class TitleCacheRecord:
    title: str
    video_id: str


class TitleCache(BaseCache[TitleCacheRecord]):
    def __init__(self, cache_file: Path = Path(config.root) / "caches/youtube_title_to_id.csv"):
        super().__init__(csv_file=cache_file, record_cls=TitleCacheRecord, key_field="title")
