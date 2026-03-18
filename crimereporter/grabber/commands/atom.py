import logging

from crimereporter.grabber.commands.article import ArticleCommand
from crimereporter.sources.source import Source
from crimereporter.utils.config import Config

logger = logging.getLogger(__name__)
config = Config()


class YoutubeAtomCommand(ArticleCommand):
    """Command to download the latest YouTube videos as articles."""

    def execute(self) -> None:
        """
        Execute the command for a single source by processing each article individually.
        """
        try:
            self.source.process_all_articles(self.overwrite)
        except Exception as e:
            logger.exception(f"Failed to process source {self.source.short_name}: {e}")

