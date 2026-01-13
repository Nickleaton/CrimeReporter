import logging

from crimereporter.grabber.article import Article
from crimereporter.grabber.exporters.exporter import Exporter
from crimereporter.utils.templates import env

logger = logging.getLogger(__name__)


class TemplateExporter(Exporter):
    """Exporter that renders an Article using a Jinja2 template."""

    def __init__(self, template_name: str, output_name: str) -> None:
        """
        Args:
            template_name (str): The Jinja2 template filename.
            output_name (str): The output filename to save the rendered content.
        """
        self.template_name = template_name
        self.output_name = output_name

    def save(self, article: Article, overwrite: bool = False) -> None:
        """Render and save the article using a template.

        Args:
            article (Article): The article to render.
            overwrite (bool): Whether to overwrite an existing file.
        """
        filename = article.directory() / self.output_name
        if filename.exists() and not overwrite:
            return
        Exporter.ensure_directory(filename)
        template = env.get_template(self.template_name)
        rendered_text = template.render(**article.to_dict())
        filename.write_text(rendered_text, encoding="utf-8")
        Exporter.log(filename)
