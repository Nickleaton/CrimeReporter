import logging

from crimereporter.grabber.exporters.template import TemplateExporter

logger = logging.getLogger(__name__)


class TextExporter(TemplateExporter):
    """Exporter that saves an Article as a text file using a template."""

    def __init__(self) -> None:
        super().__init__("template.txt", "article.txt")
