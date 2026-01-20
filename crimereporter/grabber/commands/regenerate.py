import csv
import logging
from pathlib import Path

import yaml
from yaml.parser import ParserError
from yaml.reader import ReaderError
from yaml.scanner import ScannerError

from crimereporter.grabber.commands.command import Command
from crimereporter.utils.config import Config

logger = logging.getLogger(__name__)

config = Config()


class RegenerateCommand(Command):
    """Command to generate a two-panel HTML index page from cached articles."""

    def __init__(self) -> None:
        """Initialize the IndexCommand."""
        super().__init__()

    @staticmethod
    def articles() -> list[dict]:
        articles = []
        for yaml_file in Path(config.root).glob("downloads/*/*/*/*/*/article.yaml"):
            html_file = yaml_file.with_name("article.html").relative_to(Path(config.root) / 'downloads').as_posix()

            try:
                with yaml_file.open(encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if not isinstance(data, dict):
                        logger.warning(f"Skipping invalid YAML file {yaml_file}")
                        continue
            except (ReaderError, ParserError, ScannerError, UnicodeDecodeError) as e:
                logger.error(f"Error reading YAML file {yaml_file}: {e}")
                continue
            article = {
                "datetime": data.get("datetime"),
                "title": data.get("title"),
                "url": data.get("url"),
                "source": data.get("source_short_name"),
                "html": html_file,
            }
            articles.append(article)
        articles.sort(key=lambda a: (a.get("datetime") or "", a.get("title") or ""))
        return articles

    def execute(self) -> None:
        """
        Execute the command to produce an HTML index page.

        The left panel shows date, source, and title (with icons for remote
        and local files). Records are sorted by descending date, ascending
        source, and ascending title. Clicking a local file displays it in the
        right panel.
        """
        super().execute()

        records = self.articles()
        output_csv = Path(config.root) / "caches/regenerated.csv"
        fieldnames = ["datetime", "title", "url", "source", "html"]

        # Ensure directory exists
        output_csv.parent.mkdir(parents=True, exist_ok=True)

        # Write records to CSV
        with output_csv.open(mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

        logger.info(f"Saved regenerated cache to {output_csv}")
