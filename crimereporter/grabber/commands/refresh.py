from pathlib import Path

from crimereporter.grabber.commands.article import ArticleCommand
from crimereporter.sources.source import Source


class RefreshCommand(ArticleCommand):
    """Command to refresh from local files."""

    def get_article_identifiers(self, source: Source) -> list[str]:
        return [str(p) for p in source.fetch_files()]

    def get_article(self, _: Source, identifier: str) -> str:
        return Path(identifier).read_text(encoding="utf-8")
