import logging
from pathlib import Path
from urllib.parse import unquote, urlparse

from crimereporter.grabber.article import Article
from crimereporter.grabber.exporters.exporter import Exporter
from crimereporter.grabber.fetcher import Fetcher

logger = logging.getLogger(__name__)


class FileExporter(Exporter):
    """Exporter that downloads files referenced in an Article (e.g., files)."""

    def save(self, article: Article, overwrite: bool = False) -> None:
        Exporter.ensure_directory(article.directory())
        fetcher = Fetcher()

        for url in article.files:
            parsed = urlparse(url)
            filename = Path(unquote(parsed.path)).name or "downloaded_file"
            save_path = article.directory() / filename

            if save_path.exists() and not overwrite:
                continue

            fetcher.download_file(page_url=article.url, file_url=url, save_path=save_path)
