import logging
from pathlib import Path

from crimereporter.grabber.article import Article
from crimereporter.grabber.exporters.exporter import Exporter

logger = logging.getLogger(__name__)


class SoupExporter(Exporter):
    """Exporter that saves an Article's BeautifulSoup content as raw HTML."""

    def save(self, article: Article, overwrite: bool = False) -> None:
        """Save the article's HTML content.

        Args:
            article (Article): The article to save.
            overwrite (bool): Whether to overwrite an existing file.
        """
        filename: Path = article.directory() / "raw.html"
        if filename.exists() and not overwrite:
            return
        Exporter.ensure_directory(filename)
        with filename.open("w", encoding="utf-8") as f:
            f.write(article.soup.prettify())
        Exporter.log(filename)
