import logging

from crimereporter.grabber.exporters.template import TemplateExporter

logger = logging.getLogger(__name__)


class HTMLExporter(TemplateExporter):
    """Exporter that saves an Article as an HTML file using a template."""

    def __init__(self) -> None:
        super().__init__("template.html", "article.html")
