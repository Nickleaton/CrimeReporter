import inspect
import logging
import mimetypes
import re
from abc import ABC, ABCMeta, abstractmethod
from pathlib import Path
from typing import Type

import requests
from bs4 import BeautifulSoup

from crimereporter.grabber.article import Article
from crimereporter.grabber.cache import Cache
from crimereporter.grabber.exporters.file import FileExporter
from crimereporter.grabber.exporters.html import HTMLExporter
from crimereporter.grabber.exporters.soup import SoupExporter
from crimereporter.grabber.exporters.text import TextExporter
from crimereporter.grabber.exporters.yaml import YAMLExporter
from crimereporter.grabber.fetcher import Fetcher
from crimereporter.sources.file_directory import FileDirectory
from crimereporter.sources.file_record import FileRecord, FileType
from crimereporter.utils.config import Config

logger = logging.getLogger(__name__)

config = Config()


class SourceMeta(ABCMeta):
    """Metaclass that registers all subclasses of Source."""

    registry: dict[str, Type["Source"]] = {}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if not inspect.isabstract(cls) and issubclass(cls, Source):
            SourceMeta.registry[cls.__name__] = cls

        return cls


class Source(ABC, metaclass=SourceMeta):
    """Abstract base class for all sources."""

    EXPORTER = YAMLExporter() | SoupExporter() | TextExporter() | HTMLExporter() | FileExporter()

    instances: dict[str, "Source"] = {}

    def __init__(self, short_name: str, long_name: str, root: str, directory: str) -> None:
        """Initialize a Source instance.

        Args:
            short_name (str): Short identifier for the source.
            long_name (str): Full descriptive name for the source.
            root (str): Root URL or directory for the source.
            directory (str): Directory where source files are stored.
        """
        self.short_name: str = short_name
        self.long_name: str = long_name
        self.root: str = root
        self.directory: str = directory
        self.article: Article | None = None
        self.raw: str | None = None
        self.soup: BeautifulSoup | None = None

    @classmethod
    def load_sources(cls) -> None:
        """Load sources from the YAML configuration and register them in Source.instances.

        Raises:
            ValueError: If a source type is missing or unregistered.
        """
        for entry in config.sources:
            cfg: dict[str, str] = entry["source"]
            class_name: str = cfg["source_type"]
            if not class_name:
                raise ValueError(f"No class defined for source {cfg['short_name']}")

            source_cls = SourceMeta.registry.get(class_name)
            if not source_cls:
                raise ValueError(f"No class registered for type: {class_name} source: {cfg['short_name']}")

            if inspect.isabstract(source_cls):
                logger.error(f"Cannot instantiate abstract source class: {class_name} for {cfg['short_name']}")
                raise TypeError(f"Cannot instantiate abstract source class: {class_name} for {cfg['short_name']}")

            source_data: dict[str, str] = cfg.copy()
            source_data.pop("source_type", None)
            source_instance: Source = source_cls(**source_data)
            Source.instances[cfg["short_name"]] = source_instance

    @abstractmethod
    def is_removed(self, text) -> bool:
        """Check if the article is removed from the source."""
        pass

    def get_article_from_url(self, url: str) -> Article | None:
        """
        Fetch, clean, and extract a single article from a URL.

        Args:
            url (str): URL or identifier of the article.

        Returns:
            Article | None: Extracted Article object, or None if skipped or failed.
        """
        try:
            text = self.download(url)
        except (requests.RequestException, OSError) as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

        if not text:
            logger.debug(f"No text        {url}")
            return None

        try:
            article = self.extract(text, url)
            return article
        except Exception as e:
            logger.exception(f"Failed to extract article {url}: {e}")
            return None

    def get_articles(self) -> list[Article]:
        """
        Retrieve all articles for this source by iterating over the latest URLs.
        Skips cached articles and removed articles.

        Returns:
            list[Article]: List of extracted Article objects.
        """
        articles: list[Article] = []

        for identifier in self.fetch_latest_urls():
            if Cache().is_cached(identifier):
                logger.debug("Skipping cached article: %s", identifier)
                continue

            article = self.get_article_from_url(identifier)
            if article:
                articles.append(article)

        return articles

    def process_all_articles(self, overwrite: bool) -> None:
        """Process all articles for this source."""

        for article in self.get_articles():
            self.EXPORTER.save(article, overwrite)
            article.update_cache()

    @staticmethod
    def clean_text(text: str) -> str:
        """Remove HTML tags and normalize whitespace.

        Args:
            text (str): Raw HTML text.

        Returns:
            str: Cleaned plain text with normalized newlines.
        """
        # Parse the HTML
        soup = BeautifulSoup(text, "html.parser")

        # Extract text content, keeping line breaks between elements
        text = soup.get_text(separator="\n", strip=True)

        # Collapse multiple newlines into one and trim extra spaces
        text = re.sub(r"\n+", "\n", text).strip()

        return text

    @classmethod
    def shortnames(cls) -> list[str]:
        """Return all registered source shortnames.

        Returns:
            list[str]: Sorted list of shortnames.
        """
        return sorted(cls.instances.keys())

    @classmethod
    def all_sources(cls) -> list["Source"]:
        """Return all registered source instances.

        Returns:
            list[Source]: list of source instances.
        """
        return list(cls.instances.values())

    @classmethod
    def get_source(cls, name: str) -> "Source | None":
        """Return a source instance by its short_name.

        Args:
            name (str): The short_name of the source.

        Returns:
            Optional[Source]: The source instance or None if not found.
        """
        return cls.instances.get(name)

    @staticmethod
    def get_text(url: str) -> str:
        """Fetch raw text from a URL using the Fetcher.

        Args:
            url (str): URL to fetch.

        Returns:
            str: Raw text content from the URL.
        """
        return Fetcher().fetch(url)

    @staticmethod
    def download_file(url: str, save_dir: Path) -> None:
        """Download a file from a URL and save it to a directory.

        Args:
            url (str): Full URL of the file.
            save_dir (Path): Directory where the image will be saved.
        """
        save_dir.mkdir(parents=True, exist_ok=True)

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Try to determine extension from Content-Type
            content_type = response.headers.get("Content-Type", "")
            extension = mimetypes.guess_extension(content_type.split(";")[0].strip()) or ""

            # Fall back to the URL name (may not include an extension)
            name = Path(url).name
            if not Path(name).suffix and extension:
                name += extension

            filename = save_dir / name
            filename.write_bytes(response.content)

            logger.info(f"File saved to {filename}")

        except requests.RequestException as e:
            logger.error(f"Failed to download file {url}: {e}")

    @staticmethod
    def download_image(img_url: str, save_dir: Path) -> None:
        Source.download_file(img_url, save_dir)

    @abstractmethod
    def fetch_latest_urls(self) -> list[str]:
        """Subclasses must return a list of the latest article URLs.

        Returns:
            list[str]: list of article URLs.
        """
        pass

    def fetch_files(self) -> list[Path]:
        """Return all raw HTML files for this source.

        Returns:
            list[Path]: list of Paths to raw HTML files.
        """
        glob_string: str = f"downloads/*/*/*/{self.directory}/*/raw.html"
        return list(Path(config.root).glob(glob_string))

    @abstractmethod
    def extract(self, text: str, identifier: str) -> Article:
        """Extract article data from raw text.

        Args:
            text (str): Raw HTML text.
            identifier (str): The identifier of the article.

        Returns:
            Article: Extracted article data.
        """
        pass

    def get_file_urls(self) -> list[str]:
        """Return a list of associated image URLs.

        Returns:
            list[str]: File  URLs (default empty).
        """
        return []

    def get_associated_files(self) -> FileDirectory:
        return self.get_href_files() | self.get_zip_files() | self.get_embedded_files() | self.get_video_files()

    def get_href_files(self) -> FileDirectory:
        """
        Return FileRecords for normal <a href> or <img src> URLs.
        These are external links or additional downloadable resources.
        """
        files = FileDirectory()
        for url in self.get_file_urls():
            filename = Path(url).name
            files.add(
                FileRecord(
                    filename=filename,
                    file_type=FileType.IMAGE,  # or choose a type dynamically
                    content=b"",  # placeholder; content can be fetched later
                    source=url,
                )
            )
        return files

    def get_zip_files(self) -> FileDirectory:
        return FileDirectory()

    def get_embedded_files(self) -> FileDirectory:
        return FileDirectory()

    def get_video_files(self) -> FileDirectory:
        return FileDirectory()

    @abstractmethod
    def clean(self, text: str) -> str:
        """Clean raw HTML text or soup for further processing.

        Args:
            text (str): Raw HTML text.

        Returns:
            str: Cleaned text.
        """
        pass

    def download(self, url: str) -> str:
        """Fetch and clean text from a URL.

        Args:
            url (str): URL to fetch.

        Returns:
            str: Cleaned text from the URL.
        """
        text: str = self.get_text(url)
        return self.clean(text)

    def extract_meta(self, prop: str) -> str:
        meta = self.soup.find("meta", property=prop)
        if meta and meta.has_attr("content"):
            content = meta["content"]
            if isinstance(content, list):
                # join multiple contents if necessary
                return " ".join(str(c) for c in content)
            return str(content)
        return ""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} short_name={self.short_name}>"
