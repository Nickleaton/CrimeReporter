import csv
import logging
from dataclasses import asdict, fields
from pathlib import Path
from typing import Dict, Generic, Optional, Type, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


class BaseCache(Generic[T]):
    """Generic CSV-backed message_cache manager with optional composite key support."""

    csv_file: Path
    cache: Dict[str, T]
    record_cls: Type[T]
    key_field: str  # field in record_cls that acts as dict key

    def __init__(self, csv_file: Path, record_cls: Type[T], key_field: str) -> None:
        if hasattr(self, "initialized") and self.initialized:
            return

        self.csv_file = csv_file
        self.record_cls = record_cls
        self.key_field = key_field
        self.cache = {}

        self.csv_file.parent.mkdir(parents=True, exist_ok=True)
        self.load_cache()
        self.initialized = True

    def load_cache(self) -> None:
        """Loads message_cache records from the CSV file into memory."""
        if self.csv_file.exists():
            try:
                with self.csv_file.open(newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    _ = next(reader, None)  # skip header
                    expected = len(fields(self.record_cls))
                    for row in reader:
                        if len(row) == expected:
                            rec = self.record_cls(*row)
                            key = getattr(rec, self.key_field)
                            self.cache[key] = rec
                        else:
                            logger.warning(f"Skipping malformed row in {self.csv_file}: {row}")
            except (OSError, csv.Error) as e:
                logger.warning(f"Failed to load message_cache from {self.csv_file}: {e}")

    def reload(self) -> None:
        """Reloads the message_cache from disk, replacing the current in-memory cache."""
        logger.debug(f"Reloading cache from {self.csv_file}")
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
                f.name: (getattr(record, f.name) if getattr(record, f.name) is not None else getattr(existing, f.name))
                for f in fields(self.record_cls)
            }
            record = self.record_cls(**merged)

        if existing == record:
            return  # no change

        self.cache[key] = record
        self.write_to_disk()

    def write_to_disk(self) -> None:
        """Persist all message_cache records to CSV atomically, including column headers."""
        temp_file: Path = self.csv_file.with_suffix(".tmp")
        try:
            with temp_file.open(mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # write column headers
                writer.writerow([f.name for f in fields(self.record_cls)])
                for rec in self.cache.values():
                    writer.writerow(asdict(rec).values())
            temp_file.replace(self.csv_file)
        except OSError as e:
            logger.error(f"Failed to write message_cache file {self.csv_file}: {e}")

    def clear(self) -> None:
        """Clear message_cache in memory and delete CSV file."""
        self.cache.clear()
        try:
            if self.csv_file.exists():
                self.csv_file.unlink()
        except OSError as e:
            logger.warning(f"Failed to delete message_cache file {self.csv_file}: {e}")

    def records(self) -> list[T]:
        """Return a list of cached records sorted by key."""
        return sorted(self.cache.values(), key=lambda r: getattr(r, self.key_field), reverse=True)

    def __len__(self) -> int:
        return len(self.cache)

    def __contains__(self, key: str) -> bool:
        return key in self.cache
