from dataclasses import dataclass
from pathlib import Path

from crimereporter.caches.csv_cache import CSVCache
from crimereporter.utils.config import Config

config = Config()


@dataclass
class TextCacheRecord:
    video_id: str
    text_hash: str


class TextCache(CSVCache[TextCacheRecord]):
    def __init__(
        self, cache_file: Path = Path(config.root) / "caches/youtube_text.csv"
    ):
        super().__init__(
            csv_file=cache_file, record_cls=TextCacheRecord, key_field="video_id"
        )
