import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml
from bs4 import BeautifulSoup

from crimereporter.grabber.cache import Cache
from crimereporter.utils.config import Config

logger = logging.getLogger(__name__)
config = Config()


class Article:
    """Represents a news or report article fetched from a specified source."""

    REQUIRED_KEYS: set[str] = {"datetime", "source_name", "identifier", "soup"}
    EXCLUDED_KEYS_YAML: set[str] = {"soup", "files"}

    def __init__(
        self,
        identifier: str,
        timestamp: str,
        source_name: str,
        soup: Any,
        title: str,
        url: str,
        source_short_name: str,
        files: list[str],
        article: str,
        raw: str,
    ) -> None:
        self.identifier = identifier
        self.timestamp = timestamp
        self.source_name = source_name
        self.soup = soup
        self.title = title
        self.url = url
        self.source_short_name = source_short_name
        self.files = files
        self.article = article
        self.raw = raw
        # --- derived attributes ---
        self.filenames: list[str] = [urlparse(url).path.rsplit("/", 1)[-1] for url in self.files]
        self.filename: str = (self.directory() / Path("article.html")).as_posix()
        self.raw_filename: str = self.filename.replace(".html", ".raw.html")

        raw_strip = self.raw.strip()
        if (
            raw_strip.startswith("<?xml")
            or raw_strip.startswith("<!DOCTYPE html") is False
            and raw_strip.startswith("<")
        ):
            parser = "xml"
        else:
            parser = "html.parser"

        self.soup = BeautifulSoup(self.raw, parser)

        # optional runtime attributes
        self.images: list[str] = []
        self.people: list[str] = []

    # --- Class/Factory methods ---

    def directory(self) -> Path:
        """Constructs a directory path based on the article metadata.

        Returns:
            Path: A directory path in the format:
                downloads/year/month/day/source_name/identifier
        """
        return Path(config.downloads) / self.relative_directory()

    def relative_directory(self) -> Path:
        """Constructs a relative directory path based on the article metadata."""
        return (
            Path(self.timestamp[0:4])
            / self.timestamp[5:7]
            / self.timestamp[8:10]
            / self.source_short_name
            / self.identifier
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Article":
        """Create an Article instance from a dictionary."""
        return cls(
            identifier=data.get("identifier", ""),
            timestamp=data.get("datetime", ""),
            source_name=data.get("source_name", ""),
            soup=data.get("soup"),
            title=data.get("title", ""),
            url=data.get("url", ""),
            source_short_name=data.get("source_short_name", ""),
            files=data.get("filenames", []),
            article=data.get("article", ""),
            raw=data.get("raw", ""),
        )

    @classmethod
    def load_from_yaml(cls, filename: Path) -> "Article":
        if not filename.exists():
            raise FileNotFoundError(f"YAML file not found: {filename}")
        with filename.open(encoding="utf-8") as f:
            loaded_data = yaml.safe_load(f)
        if not isinstance(loaded_data, dict):
            raise ValueError(f"Invalid YAML content in {filename}")
        return cls.from_dict(loaded_data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to a dictionary suitable for exporting, excluding transient and unwanted keys."""
        excluded_keys = self.EXCLUDED_KEYS_YAML | {"people", "raw_filename"}
        return {k: v for k, v in vars(self).items() if k not in excluded_keys}

    # --- Validation ---

    def validate(self) -> None:
        missing = {k for k in self.REQUIRED_KEYS if not getattr(self, k)}
        if missing:
            logger.error(f"Missing required keys: {missing} {self.source_name} {self.identifier}")
            raise ValueError(f"Missing required keys in article data: {missing}")

    # --- Existing methods (unchanged except using attributes instead of data) ---
    # save_soup, save_yaml, save_text, save_html, save_images, etc.

    def __repr__(self) -> str:
        return f"Article(identifier={self.identifier or 'unknown'}, source_name={self.source_name or 'unknown'})"

    def __str__(self) -> str:
        lines = [
            f"  {k} = {getattr(self, k)!r}"
            for k in vars(self)
            if k not in {"people", "raw_filename"} | self.EXCLUDED_KEYS_YAML
        ]
        return "\n".join(lines)

    def update_cache(self) -> None:
        """Updates the message_cache with article metadata."""
        filename = self.relative_directory() / "article.html"
        filename_posix = Path(*filename.parts[1:]).as_posix()
        Cache().add(
            self.timestamp,
            self.title,
            self.url,
            self.source_short_name,
            filename_posix,
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        )
