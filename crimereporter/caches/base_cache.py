from abc import ABC, abstractmethod
import logging
from dataclasses import asdict, fields
from pathlib import Path
from typing import Dict, Generic, Optional, Type, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


class BaseCache(Generic[T], ABC):
    """Generic CSV-backed message_cache manager with optional composite key support."""

    csv_file: Path
    cache: Dict[str, T]
    record_cls: Type[T]
    key_field: str  # field in record_cls that acts as dict key

    def __init__(self, record_cls: Type[T], key_field: str) -> None:
        if hasattr(self, "initialized") and self.initialized:
            return

        self.record_cls = record_cls
        self.key_field = key_field
        self.cache = {}

        self.load_cache()
        self.initialized = True

    @abstractmethod
    def load_cache(self) -> None:
        pass

    @abstractmethod
    def persist(self) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    def reload(self) -> None:
        """Reloads the message_cache from disk, replacing the current in-memory cache."""
        logger.debug("Reloading cache")
        self.cache.clear()
        self.load_cache()

    def get(self, *key_parts: str) -> Optional[T]:
        """Retrieve a cached record. Accepts single or composite keys."""
        key = ":".join(key_parts) if len(key_parts) > 1 else key_parts[0]
        return self.cache.get(key)

    def add(self, record: T, *extra_key_parts: str) -> None:
        """Add or update a message_cache record, optionally using composite key parts."""
        key = getattr(record, self.key_field)
        if extra_key_parts:
            key = ":".join([key, *extra_key_parts])

        existing = self.cache.get(key)

        # merge None fields
        if existing is not None:
            merged = {
                f.name: (
                    getattr(record, f.name)
                    if getattr(record, f.name) is not None
                    else getattr(existing, f.name)
                )
                for f in fields(self.record_cls)
            }
            record = self.record_cls(**merged)

        if existing == record:
            return  # no change

        self.cache[key] = record
        self.persist()

    def records(self) -> list[T]:
        """Return a list of cached records sorted by key."""
        return sorted(
            self.cache.values(), key=lambda r: getattr(r, self.key_field), reverse=True
        )

    def __len__(self) -> int:
        return len(self.cache)

    def __contains__(self, key: str) -> bool:
        return key in self.cache
