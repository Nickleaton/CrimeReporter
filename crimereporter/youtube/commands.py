import hashlib
import json
import logging
import pickle
from pathlib import Path
from typing import Any, BinaryIO, Optional, cast

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from crimereporter.caches.metadata import MetadataCache
from crimereporter.caches.text import TextCache
from crimereporter.caches.thumbnail import ThumbnailCache
from crimereporter.caches.title import TitleCache
from crimereporter.news.commands.simple import SimpleCommand
from crimereporter.utils.config import Config
from crimereporter.utils.templates import env

logger = logging.getLogger(__name__)

call_logger = logging.getLogger("call.logger.youtube")

config = Config()
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

titles_cache = TitleCache()
thumbnails_cache = ThumbnailCache()
texts_cache = TextCache()
metadata_cache = MetadataCache()


class YoutubeCommand(SimpleCommand):

    def __init__(self, input_file: Path, orientation: str, video_id: str | None = None) -> None:
        super().__init__(input_file, orientation)
        self.youtube = self.build_youtube_service()
        self.title = f"{self.script.parsed['Date']}: {self.script.parsed['Title']}"
        # Use provided video_id if given, otherwise try to find it
        self.video_id = video_id or self.find_video_by_title(self.title)
        self.description = env.get_template("description.txt").render(**self.script.parsed)

        # Filenames
        self.thumbnail_file = self.input_file.parent / "output" / f"{self.orientation}.png"
        self.text_file = self.input_file.parent / "output" / "text.txt"
        self.video_file = self.input_file.parent / "output" / f"{self.orientation}.mp4"

        # Hashes
        self.thumbnail_hash = self.calculate_file_hash(self.thumbnail_file)
        self.text_hash = self.calculate_file_hash(self.text_file)
        self.metadata_hash = self.calculate_metadata_hash()

    @staticmethod
    def get_credentials() -> Credentials:
        """Load or refresh YouTube API credentials."""
        token_file = Path(config.root) / "keys/token.pkl"
        creds: Optional[Credentials] = None

        if token_file.exists():
            with token_file.open("rb") as f:
                creds = cast(Credentials, pickle.load(f))

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                key_file = f'{config.root}/keys/youtube_secrets.json'
                flow = InstalledAppFlow.from_client_secrets_file(key_file, SCOPES)
                creds = flow.run_local_server(port=0)
            with token_file.open("wb") as f:
                # call_logger.info(f"Saving credentials to {token_file}")
                # noinspection PyTypeChecker
                pickle.dump(creds, cast(BinaryIO, f))
        return creds

    def build_youtube_service(self):
        # call_logger.info(f"Build Service")
        creds = self.get_credentials()
        return build("youtube", "v3", credentials=creds)

    def find_video_by_title(self, title: str) -> Optional[str]:
        """Return video_id if a video with the given title exists, else None."""

        cached_record = titles_cache.get(title)
        if cached_record:
            return cached_record.video_id  # access the dataclass field

        if config.youtube.find_by_title:
            call_logger.info(f"Find {title}")
            request = self.youtube.search().list(
                part="id",  # correct YouTube API field
                forMine=True,
                type="video",
                q=title,
                maxResults=1,
            )
            response = request.execute()
            items = response.get("items", [])
            if items:
                video_id = items[0]["id"]["videoId"]  # correct path
                # store as dataclass
                from crimereporter.caches.title import TitleCacheRecord

                titles_cache.add(TitleCacheRecord(title=title, video_id=video_id))
                return video_id
        return None

    def create_metadata(self) -> dict[str, Any]:
        # call_logger.info(f"Create Meta {self.title}")
        body: dict[str, Any] = {
            "snippet": {
                "title": self.title,
                "description": self.description,
                "tags": self.script.parsed.get("Tags", []),
                "categoryId": "25",
                "defaultLanguage": "en",
                "defaultAudioLanguage": "en",
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
            },
        }

        if self.video_id:
            body["id"] = self.video_id

        return body

    @staticmethod
    def calculate_file_hash(file_path: Path) -> str:
        """Compute SHA256 hash of a file."""
        if not file_path.exists():
            return ""
        h = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def calculate_metadata_hash(self) -> str:
        """Compute SHA256 hash of video metadata."""
        dict_string = json.dumps(self.create_metadata(), sort_keys=True)
        return hashlib.sha256(dict_string.encode()).hexdigest()
