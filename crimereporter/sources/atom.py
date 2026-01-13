import logging
from datetime import datetime

import feedparser

from crimereporter.grabber.article import Article
from crimereporter.sources.file_directory import FileDirectory
from crimereporter.sources.source import Source
from crimereporter.utils.config import Config
from crimereporter.utils.templates import env

logger = logging.getLogger(__name__)
config = Config()


class YouTubeAtomSource(Source):
    @classmethod
    def load_atom_sources(cls):
        for entry in config.sources:
            cfg: dict[str, str] = entry["source"]
            if "channel_id" not in cfg:
                continue
            source_data: dict[str, str] = cfg.copy()
            source_data.pop("source_type", None)
            source_instance: Source = cls(**source_data)
            Source.instances[f"{cfg['short_name']} YT"] = source_instance

    def clean(self, text: str) -> str:
        return text

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

    @staticmethod
    def text(entry, tag_name: str) -> str:
        """Return the text of a tag if it exists, else an empty string."""
        tag = entry.find(tag_name)
        return tag.text.strip() if tag and tag.text else ""

    @staticmethod
    def to_datetime(value: str) -> str:
        """Convert Atom datetime to 'YYYY-MM-DD HH:MM'."""
        if not value:
            return ""
        try:
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            dt = datetime.fromisoformat(value)
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            logger.warning(f"Invalid datetime format: {value!r}")
            return value

    def fetch_latest_urls(self) -> list[str]:
        return [f"https://www.youtube.com/feeds/videos.xml?channel_id={self.channel_id}"]

    @staticmethod
    def entry_to_text(entry) -> str:
        template = env.get_template("entry_template.xml")
        return template.render(entry=entry)

    def process_entry(self, entry) -> Article:
        """Convert a single <entry> element into an Article instance."""
        video_id = entry["yt_videoid"]
        title = entry["title"]
        author = entry["author_detail"]["name"]
        url = entry["link"]
        published = self.to_datetime(entry["published"])
        description = entry["summary_detail"]["value"]
        raw = self.entry_to_text(entry)
        return Article(
            identifier=video_id,
            timestamp=self.to_datetime(published),
            source_name=author or "YouTube",
            source_short_name=self.short_name,
            title=title,
            url=url,
            files=[],
            article=description or "",
            soup=entry,
            raw=raw,
        )

    def get_articles(self) -> list[Article]:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={self.channel_id}"
        logger.info(f"Fetching       {url}")

        feed = feedparser.parse(url)
        if feed.bozo:
            logger.error(f"Error parsing Atom feed: {feed.bozo_exception}")
            return []

        articles = []
        for entry in feed.entries:
            articles.append(self.process_entry(entry))

        return articles

    def is_removed(self, text) -> bool:
        """YouTube Atom entries are never marked as 'removed'."""
        return False

    def extract(self, text: str, identifier: str) -> Article:
        """Not used for YouTube feeds."""
        raise NotImplementedError("YouTubeAtomSource does not extract HTML text directly.")

    def get_href_files(self) -> FileDirectory:
        """Return FileRecords for normal <a href> or <img src> URLs."""
        return FileDirectory()

    def get_zip_files(self) -> FileDirectory:
        return FileDirectory()

    def get_embedded_files(self) -> FileDirectory:
        """Return FileRecords for base64-embedded images (already saved to disk)."""
        return FileDirectory()

    def get_video_files(self) -> FileDirectory:
        """Return FileRecords for associated video files (YouTube, MP4, etc.)."""
        return FileDirectory()
