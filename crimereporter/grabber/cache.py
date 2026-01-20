import csv
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

from crimereporter.utils.config import Config
from crimereporter.utils.singleton import singleton

logger = logging.getLogger(__name__)

config = Config()


@dataclass(frozen=True)
class CacheRecord:
    """Represents a single message_cache record.

    Attributes:
        date (str): Date of the record (e.g., creation date).
        title (str): Title of the content.
        url (str): URL of the content.
        source_name (str): Name of the source (category or source).
        filename (str): Local filename associated with the content.
    """

    date: str
    title: str
    url: str
    source_name: str
    filename: str
    timestamp: str


@singleton
class Cache:
    """Manages a CSV-backed message_cache of URL records."""

    csv_file: Path
    cache: Dict[str, CacheRecord]

    def __init__(self, csv_file: Path = Path(config.root) / "caches/cache.csv") -> None:
        # Only load message_cache once per singleton instance
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.csv_file = csv_file
        self.cache = {}
        self.load_cache()
        self.initialized = True

    def load_cache(self) -> None:
        """Loads message_cache records from the CSV file into memory.

        Skips malformed rows and logs warnings.
        """
        if self.csv_file.exists():
            try:
                with self.csv_file.open(newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    next(reader, None)
                    for row in reader:
                        if len(row) == 6:
                            date, title, url, source_name, filename, timestamp = row
                            self.cache[url] = CacheRecord(date, title, url, source_name, filename, timestamp)
                        else:
                            logger.warning(f"Skipping malformed row in {self.csv_file}: {row}")
            except (OSError, csv.Error) as e:
                logger.warning(f"Failed to load message_cache from {self.csv_file}: {e}")

    def is_cached(self, url: str) -> bool:
        """Checks if a URL is already in the message_cache.

        Args:
            url (str): The URL to check.

        Returns:
            bool: True if the URL is cached, False otherwise.
        """
        return url in self.cache

    def get_cached_record(self, url: str) -> Optional[CacheRecord]:
        """Retrieves the cached record for a URL, if it exists.

        Args:
            url (str): The URL whose record is requested.

        Returns:
            Optional[CacheRecord]: The message_cache record if found, otherwise None.
        """
        return self.cache.get(url)

    def add(
        self,
        date: str,
        title: str,
        url: str,
        source_name: str,
        filename: str,
        timestamp: str,
    ) -> None:
        """Adds or updates a message_cache record and writes the updated message_cache to disk.

        If the URL already exists, the record is updated (upsert behavior).

        Args
            date (str): Date of the record (e.g., creation date).
            title (str): Title of the content.
            url (str): URL of the content.
            source_name (str): Name of the source (category or source).
            filename (str): Local filename associated with the content.
        """
        # Upsert the record
        record = CacheRecord(date, title, url, source_name, filename, timestamp)
        self.cache[url] = record

        temp_file: Path = self.csv_file.with_suffix(".tmp")
        try:
            with temp_file.open(mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for rec in self.cache.values():
                    writer.writerow(
                        [
                            rec.date,
                            rec.title,
                            rec.url,
                            rec.source_name,
                            Path(rec.filename).as_posix(),
                            rec.timestamp,
                        ]
                    )
            temp_file.replace(self.csv_file)
        except OSError as e:
            logger.error(f"Failed to write message_cache file {self.csv_file}: {e}")

    def clear(self) -> None:
        """Clears the message_cache both in memory and deletes the CSV file from disk."""
        self.cache.clear()
        try:
            if self.csv_file.exists():
                self.csv_file.unlink()
        except OSError as e:
            logger.warning(f"Failed to delete message_cache file {self.csv_file}: {e}")

    def records(self) -> list[CacheRecord]:
        cutoff = datetime.now() - timedelta(days=config.index_days)

        return sorted(
            (r for r in self.cache.values() if datetime.fromisoformat(r.timestamp) >= cutoff),
            key=lambda r: datetime.fromisoformat(r.timestamp),
            reverse=True,
        )

    def __len__(self) -> int:
        """Returns the number of cached records.

        Returns:
            int: Number of records in the message_cache.
        """
        return len(self.cache)

    def __contains__(self, url: str) -> bool:
        """Checks if a URL exists in the message_cache using the `in` keyword.

        Args:
            url (str): The URL to check.

        Returns:
            bool: True if the URL exists in the message_cache, False otherwise.
        """
        return url in self.cache
