import logging
from abc import ABC, abstractmethod

from bs4 import BeautifulSoup

from crimereporter.grabber.article import Article
from crimereporter.sources.source import Source
from crimereporter.utils.config import Config

logger = logging.getLogger(__name__)

config = Config()


class Force(Source, ABC):
    def __init__(
        self,
        short_name: str,
        long_name: str,
        root: str,
        directory: str,
        youtube_id: str | None = None,
        channel_id: str | None = None,
    ):
        super().__init__(short_name, long_name, root, directory)
        self.youtube_id = youtube_id
        self.channel_id = channel_id

    def extract(self, raw: str, identifier: str) -> Article:
        self.soup = BeautifulSoup(raw, "html.parser")
        files = self.get_associated_files()
        print(files)
        return Article(
            identifier=self.extract_id(),
            timestamp=self.extract_date(),
            source_name=self.short_name,
            soup=self.soup,
            title=self.extract_title(),
            url=identifier,
            source_short_name=self.short_name,
            files=self.get_file_urls(),
            article=self.extract_text(),
            raw=raw,
        )

    @abstractmethod
    def extract_date(self) -> str:
        pass

    @abstractmethod
    def extract_id(self) -> str:
        pass

    @abstractmethod
    def extract_name(self) -> str:
        pass

    @abstractmethod
    def extract_title(self) -> str:
        pass

    @abstractmethod
    def extract_text(self) -> str:
        pass

    def is_removed(self, text: str) -> bool:
        return False
