import logging

from crimereporter.grabber.commands.article import ArticleCommand
from crimereporter.sources.source import Source
from crimereporter.utils.config import Config

logger = logging.getLogger(__name__)
config = Config()


class YoutubeAtomCommand(ArticleCommand):
    """Command to download the latest YouTube videos as articles."""

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
        sources = [s for s in YoutubeAtomCommand.all_sources() if self.source in (None, s.short_name)]
        if not sources:
            logger.warning(f"No sources matched: {self.source}")
            return
        super().execute()
        for source in sources:
            self.execute_source(source)
