import logging
from pathlib import Path

import httpx
import yaml
from atproto import Client
from atproto_client.exceptions import InvokeTimeoutError

from crimereporter.caches.media_cache import MediaCacheRecord
from crimereporter.caches.message_cache import MessageCache, MessageCacheRecord
from crimereporter.posters.poster import Poster
from crimereporter.utils.base import ImageBase
from crimereporter.utils.config import Config

logger = logging.getLogger(__name__)

config = Config()


class BlueskyPoster(Poster):
    """Poster implementation for Bluesky, with optional media upload."""

    def __init__(self):
        super().__init__()
        self.api = Client()
        creds_path = Path(config.root) / "keys/bluesky.yaml"
        creds = yaml.safe_load(creds_path.read_text(encoding="utf-8"))
        self.api.login(creds["username"], creds["password"])
        self.message_cache = MessageCache(Path("caches") / f"{self.name}_messages.csv")

    def post_message(
        self,
        video_id: str,
        video_title: str,
        message: str,
        image_path: Path | None = None,
    ):
        """Post a message with optional media to Bluesky, idempotent per video_id."""

        use_image_path = None
        if image_path:
            use_image_path = ImageBase.resize_for_upload(image_path, config.bluesky.maximum_image_size, self.name)

        # Skip if already posted for this video
        if self.message_cache.get(video_id):
            logger.info(f"[{self.name}] Skipping video {video_id} (already posted)")
            return

        try:
            embed = None
            if use_image_path:
                media_id = self.upload_media(use_image_path)
                if not media_id:
                    logger.warning(f"[{self.name}] Media upload failed, message will not be posted")
                    return  # Stop if media didn't upload

                embed = {
                    "$type": "app.bsky.embed.images",
                    "images": [{"image": media_id, "alt": f"Image for message: {message}"}],
                }

            self.api.send_post(message, embed=embed)

        except (InvokeTimeoutError, httpx.RequestError) as e:
            logger.error(f"[{self.name}] Failed to post to Bluesky: {e}")
            return

        # Add record to cache using video_id as key
        self.message_cache.add(MessageCacheRecord(video_id=video_id, video_title=video_title, message=message))
        logger.info(f"[{self.name}] Posted video {video_id}")

    def upload_media(self, image_path: Path) -> str | None:
        """Upload media to Bluesky and return a BlobRef. Uses media_cache to avoid re-uploading."""

        cached = self.media_cache.get(image_path)
        if cached:
            logger.info(f"[{self.name}] Using cached media")
            return cached.media_id

        if not image_path.exists():
            logger.warning(f"[{self.name}] File does not exist: {image_path}")
            return None

        try:
            with image_path.open("rb") as f:
                response = self.api.com.atproto.repo.upload_blob(data=f.read())

            blob_ref = response.blob
            self.media_cache.add(MediaCacheRecord(filename=str(image_path), media_id=blob_ref))
            logger.info(f"[{self.name}] Uploaded media")
            return blob_ref

        except (InvokeTimeoutError, httpx.RequestError) as e:
            logger.exception(f"[{self.name}] Failed to upload media {image_path}: {e}")
            return None
