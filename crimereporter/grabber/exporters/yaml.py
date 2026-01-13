import logging
from pathlib import Path

import yaml

from crimereporter.grabber.article import Article
from crimereporter.grabber.exporters.exporter import Exporter

logger = logging.getLogger(__name__)


class YAMLExporter(Exporter):
    """Exporter that saves an Article as a YAML file."""

    def save(self, article: Article, overwrite: bool = False) -> None:
        """Saves the article as a YAML file.

        Args:
            article (Article): The article to save.
            overwrite (bool): If True, overwrite existing files. Defaults to False.
        """
        filename: Path = article.directory() / "article.yaml"

        # Skip saving if file exists and overwrite is False
        if filename.exists() and not overwrite:
            return

        self.ensure_directory(filename)

        # Prepare the data for saving
        data_to_save = article.to_dict()
        data_to_save.pop("raw", None)
        data_to_save["filename"] = str(filename)
        data_to_save["raw_filename"] = str(article.directory() / "raw.html")

        # Write YAML file
        with filename.open("w", encoding="utf-8") as f:
            yaml.dump(data_to_save, f, sort_keys=False, allow_unicode=True)

        self.log(filename)
