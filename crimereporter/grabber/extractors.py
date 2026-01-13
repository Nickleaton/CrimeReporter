from abc import ABC, abstractmethod

import trafilatura
from newspaper import Article


def safe_get(obj, attr, default=None):
    """Safely get attribute from metadata objects."""
    return getattr(obj, attr, default) if obj else default


class Extractor(ABC):
    """Abstract base class for text extractors."""

    registry: dict[str, type] = {}

    def __init_subclass__(cls, **kwargs):
        """Automatically register non-abstract subclasses using a clean name."""
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "__abstractmethods__", False):
            key = cls.__name__
            if key.endswith("Extractor"):
                key = key[: -len("Extractor")]
            cls.registry[key.lower()] = cls

    @classmethod
    def create(cls, name: str) -> "Extractor":
        key = name.lower()
        if key not in cls.registry:
            raise ValueError(f"Unknown extractor: {name}")
        return cls.registry[key]()

    @classmethod
    def names(cls) -> list[str]:
        return list(cls.registry.keys())

    @abstractmethod
    def extract(self, text: str) -> dict:
        """Extract metadata and text from raw string."""
        pass


class TrafilaturaExtractor(Extractor):
    """Extract text using trafilatura."""

    def extract(self, text: str) -> dict:
        extracted_text = trafilatura.extract(text)
        if not extracted_text:
            return {"text": "", "title": None, "author": None, "date": None}

        meta = trafilatura.extract_metadata(text)
        return {
            "text": extracted_text,
            "title": safe_get(meta, "title"),
            "author": safe_get(meta, "author"),
            "date": safe_get(meta, "date"),
        }


class NewspaperExtractor(Extractor):
    """Extract text using newspaper 3k."""

    def extract(self, text: str) -> dict:
        article = Article("")  # URL not needed
        article.set_html(text)
        article.parse()

        pd = article.publish_date
        return {
            "text": article.text,
            "title": article.title,
            "author": article.authors,
            "date": pd.isoformat() if hasattr(pd, "isoformat") else pd,
            "top_image": article.top_image,
            "movies": article.movies,
        }
