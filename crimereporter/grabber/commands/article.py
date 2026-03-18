import logging
from abc import ABC

from crimereporter.grabber.commands.command import Command
from crimereporter.sources.source import Source

logger = logging.getLogger(__name__)


class ArticleCommand(Command, ABC):
    """Base class for commands that process articles."""

    def __init__(self, overwrite: bool, source: Source) -> None:
        """Initialize the ArticleCommand."""
        super().__init__()
        self.overwrite = overwrite
        self.source = source

    def execute(self) -> None:
        """
        Execute the command for a single source by processing each article individually.
        """
        try:
            self.source.process_all_articles(self.overwrite)
        except Exception as e:
            logger.exception(f"Failed to process source {self.source.short_name}: {e}")
