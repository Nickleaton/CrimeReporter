from dataclasses import dataclass
from pathlib import Path

from crimereporter.caches.csv_cache import CSVCache
from crimereporter.utils.config import Config
from crimereporter.utils.singleton import singleton

config = Config()


@dataclass(frozen=True)
class AudioCacheRecord:
    renderer: str
    text_hash: str
    language: str | None = None
    voice: str | None = None
    file_path: str = ""
    size: int = 0
    text: str = ""

    @property
    def composite_key(self) -> str:
        """Composite key including renderer, language, voice, and text hash."""
        lang = self.language or ""
        v = self.voice or ""
        return f"{self.renderer}:{lang}:{v}:{self.text_hash}"


@singleton
class AudioCache(CSVCache[AudioCacheRecord]):
    """Cache for audio segments supporting composite keys."""

    def __init__(self) -> None:
        super().__init__(
            csv_file=Path(config.root) / "caches/audio.csv",
            record_cls=AudioCacheRecord,
            key_field="composite_key",  # BaseCache will use this field as key
        )
