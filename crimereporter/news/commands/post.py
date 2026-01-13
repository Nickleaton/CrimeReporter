import logging
import re
from abc import ABC, abstractmethod
from pathlib import Path

from jinja2 import Template

from crimereporter.caches.title import TitleCache
from crimereporter.news.commands.simple import SimpleCommand
from crimereporter.posters.bluesky import BlueskyPoster
from crimereporter.posters.poster import Poster
from crimereporter.posters.xtwitter import XPoster
from crimereporter.utils.templates import env

titles_cache = TitleCache()

logger = logging.getLogger(__name__)


class PostCommand(SimpleCommand, ABC):
    URL_PATTERN = re.compile(r"https?://\S+")

    def title(self) -> str:
        return f"{self.script.parsed['Date']}: {self.script.parsed['Title']}"

    def video_id(self) -> str | None:
        key = self.title()
        titles_cache.reload()
        record = titles_cache.get(key)
        if not record:
            logger.warning(f"Video ID not found for {key}")
            return None
        return record.video_id

    def message(self) -> str | None:
        render_data = dict(self.script.parsed)

        # Remove URLs from the description
        description = render_data.get("description", "")
        render_data["description"] = self.URL_PATTERN.sub("", description)

        render_data["video_id"] = self.video_id()

        return self.template.render(**render_data)

    @property
    def image_file(self) -> Path:
        return self.script.filepath.parent / "output/landscape.png"

    def run(self) -> None:
        message = self.message()
        if not message:
            return
        self.poster.post_message(self.video_id(), self.title(), message, self.image_file)

    @property
    @abstractmethod
    def template(self) -> Template:
        raise NotImplementedError

    @property
    @abstractmethod
    def poster(self) -> Poster:
        raise NotImplementedError


class XPostCommand(PostCommand):

    @property
    def poster(self) -> Poster:
        return XPoster()

    @property
    def template(self) -> Template:
        return env.get_template("post.x.template")


class BlueskyPostCommand(PostCommand):

    @property
    def poster(self) -> Poster:
        return BlueskyPoster()

    @property
    def template(self) -> Template:
        return env.get_template("post.bluesky.template")
