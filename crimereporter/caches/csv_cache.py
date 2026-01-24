import csv
import logging
from pathlib import Path
from typing import Dict, Generic, Optional, Type, TypeVar
from dataclasses import asdict, fields

from crimereporter.caches.base_cache import BaseCache

logger = logging.getLogger(__name__)
T = TypeVar("T")


class CSVCache(BaseCache[T], Generic[T]):
    """CSV-backed cache implementation with optional composite keys."""

    def __init__(self, csv_file: Path, record_cls: Type[T], key_field: str) -> None:
        self.csv_file = csv_file
        self.csv_file.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(record_cls, key_field)


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
                            logger.warning(
                                f"Skipping malformed row in {self.csv_file}: {row}"
                            )
            except (OSError, csv.Error) as e:
                logger.warning(
                    f"Failed to load message_cache from {self.csv_file}: {e}"
                )

    def persist(self) -> None:
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