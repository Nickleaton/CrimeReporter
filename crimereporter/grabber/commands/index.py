import logging
import webbrowser
from pathlib import Path

from crimereporter.grabber.cache import Cache
from crimereporter.grabber.commands.command import Command
from crimereporter.sources.source import Source
from crimereporter.utils.config import Config
from crimereporter.utils.templates import env

logger = logging.getLogger(__name__)

config = Config()


class IndexCommand(Command):
    """Command to generate a two-panel HTML index page from cached articles."""

    def __init__(self) -> None:
        """Initialize the IndexCommand."""
        super().__init__()

    def execute(self) -> None:
        """
        Execute the command to produce an HTML index page.

        The left panel shows date, source, and title (with icons for remote
        and local files). Records are sorted by descending date, ascending
        source, and ascending title. Clicking a local file displays it in the
        right panel.
        """
        super().execute()

        output_html: Path = Path(config.downloads) / Path("index.html")
        template = env.get_template("index_template.html")

        html_content = template.render(records=Cache().records(), sources=Source.shortnames())
        output_html.write_text(html_content, encoding="utf-8")
        logger.info(f"Saved INDEX    {output_html}")

        webbrowser.open(config.pages.index)
