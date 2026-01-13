import logging

from crimereporter.grabber.article import Article
from crimereporter.grabber.exporters.exporter import Exporter

logger = logging.getLogger(__name__)


class ComposedExporter(Exporter):
    """Exporter that combines multiple exporters into a single composite exporter.

    This class implements the Composite design pattern, allowing multiple
    exporters to be chained together using the ``|`` operator.
    """

    def __init__(self, *exporters: Exporter) -> None:
        """Initializes the composite exporter.

        Args:
            *exporters (Exporter): Exporter instances to combine in sequence.
        """
        self.exporters: list[Exporter] = list(exporters)

    def save(self, article: Article, overwrite: bool = False) -> None:
        """Saves the given article using all combined exporters.

        Args:
            article (Article): The article to export.
            overwrite (bool): If True, overwrite existing files. Defaults to False.
        """
        for exporter in self.exporters:
            exporter.save(article, overwrite)

    def __or__(self, other: Exporter) -> "ComposedExporter":
        """Combines this exporter with another using the ``|`` operator.

        Args:
            other (Exporter): The exporter or composite exporter to combine with.

        Returns:
            ComposedExporter: A new composite exporter including both exporters.

        Raises:
            TypeError: If the operand is not an instance of ``Exporter`` or ``CompositeExporter``.
        """
        if isinstance(other, ComposedExporter):
            return ComposedExporter(*self.exporters, *other.exporters)
        if isinstance(other, Exporter):
            return ComposedExporter(*self.exporters, other)
        raise TypeError(f"Cannot combine ComposedExporter with {type(other).__name__}")

    def __ror__(self, other: Exporter) -> "ComposedExporter":
        """Combines another exporter with this one using the reversed ``|`` operator.

        Args:
            other (Exporter): The exporter or composite exporter to combine with.

        Returns:
            ComposedExporter: A new composite exporter including both exporters.

        Raises:
            TypeError: If the operand is not an instance of ``Exporter`` or ``CompositeExporter``.
        """
        if isinstance(other, ComposedExporter):
            return ComposedExporter(*other.exporters, *self.exporters)
        if isinstance(other, Exporter):
            return ComposedExporter(other, *self.exporters)
        raise TypeError(f"Cannot combine ComposedExporter with {type(other).__name__}")
