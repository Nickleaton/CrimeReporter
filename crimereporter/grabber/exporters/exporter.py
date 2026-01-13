from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from crimereporter.grabber.exporters.composed import ComposedExporter

from crimereporter.grabber.article import Article

logger = logging.getLogger(__name__)


class Exporter(ABC):
    """Abstract base class for all article exporters."""

    @staticmethod
    def ensure_directory(filename: Path) -> None:
        """Ensure that the parent directory of a file exists.

        Args:
            filename (Path): The file path whose parent directory should be created.
        """
        filename.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def log(filename: Path) -> None:
        """Log that a file has been saved.

        Args:
            filename (Path): The path of the file saved.
        """
        logger.info(f"Saved {filename.suffix.upper()[1:]:5}    {filename}")

    @abstractmethod
    def save(self, article: Article, overwrite: bool = False) -> None:
        """Save the article to a file.

        Args:
            article (Article): The article instance to save.
            overwrite (bool): If True, overwrite existing files. Defaults to False.
        """
        raise NotImplementedError

    def __or__(self, other: Exporter) -> ComposedExporter:
        """Combine this exporter with another using the | operator.

        Args:
            other (Exporter): Another exporter to combine with.

        Returns:
            ComposedExporter: A composite exporter combining both exporters.
        """
        from crimereporter.grabber.exporters.composed import ComposedExporter

        if isinstance(other, Exporter):
            return ComposedExporter(self, other)
        raise TypeError(f"Cannot combine Exporter with {type(other).__name__}")

    def __ror__(self, other: Exporter) -> ComposedExporter:
        """Combine another exporter with this one using reversed | operator.

        Args:
            other (Exporter): Another exporter to combine with.

        Returns:
            ComposedExporter: A composite exporter combining both exporters.
        """
        from crimereporter.grabber.exporters.composed import ComposedExporter

        if isinstance(other, Exporter):
            return ComposedExporter(other, self)
        raise TypeError(f"Cannot combine Exporter with {type(other).__name__}")
