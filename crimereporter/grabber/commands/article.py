import logging
from abc import ABC

from crimereporter.grabber.commands.command import Command
from crimereporter.sources.source import Source

logger = logging.getLogger(__name__)


class ArticleCommand(Command, ABC):
    """Base class for commands that process articles."""

    def __init__(self, overwrite: bool, source: str | None = None) -> None:
        """Initialize the ArticleCommand."""
        super().__init__()
        self.overwrite = overwrite
        self.source = source

    def execute_source(self, source: Source) -> None:
        """
        Execute the command for a single source by processing each article individually.

        Args:
            source (Source): The source to be processed.
        """
        try:
            source.process_all_articles(self.overwrite)
        except Exception as e:
            logger.exception(f"Failed to process source {source.short_name}: {e}")

    def execute(self) -> None:
        """Execute for all sources (or just one if specified)."""
        sources = [s for s in Source.all_sources() if self.source in (None, s.short_name)]
        if not sources:
            logger.warning(f"No sources matched: {self.source}")
            return
        super().execute()
        for source in sources:
            self.execute_source(source)
