from crimereporter.grabber.commands.article import ArticleCommand
from crimereporter.sources.source import Source


class DownloadCommand(ArticleCommand):
    """Command to download the latest Met Police articles."""

    def get_article_identifiers(self, source: Source) -> list[str]:
        """
        Obtain the latest article identifiers from the source.

        Args:
            source (Source): The source to query for identifiers.

        Returns:
            list[str]: A list of URLs identifying the latest articles.
        """
        return source.fetch_latest_urls()

    def get_article(self, source: Source, identifier: str) -> str | None:
        """
        Download a single article’s content.

        Args:
            source (Source): The source from which to download the article.
            identifier (str): The article’s identifier (such as its URL).

        Returns:
            str | None: The text of the article if downloaded successfully; None otherwise.
        """
        return source.download(identifier)
