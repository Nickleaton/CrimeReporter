import json
import logging
from pathlib import Path

import requests
import yaml

from crimereporter.caches.media_cache import MediaCacheRecord
from crimereporter.caches.message_cache import MessageCacheRecord
from crimereporter.posters.poster import Poster
from crimereporter.utils.config import Config

logger = logging.getLogger(__name__)

config = Config()


class FacebookPoster(Poster):
    """Poster implementation for posting to Facebook Pages with optional media."""

    def __init__(self):
        super().__init__()
        creds_path = Path(config.key_directory) / Path("facebook.yaml")
        creds = yaml.safe_load(creds_path.read_text(encoding="utf-8"))

        required = {"page_id", "access_token"}
        missing = required - creds.keys()
        if missing:
            logger.fatal(f"Missing Facebook API credentials: {missing}")
            raise RuntimeError(f"Missing Facebook API credentials: {missing}")

        self.page_id = creds["page_id"]
        self.access_token = creds["access_token"]
        self.graph_url = f"https://graph.facebook.com/v17.0/{self.page_id}"

    def post_message(self, message: str, image_path: Path | None = None):
        """
        Post a message with optional media to Facebook.
        Message-level idempotency is enforced using message_cache.
        """
        # Idempotency key
        cache_key = message if image_path is None else f"{message}:{image_path}"

        if self.message_cache.get(cache_key):
            logger.info(f"[{self.name}] Skip {cache_key} (already posted)")
            return

        try:
            if image_path:
                # Upload photo first
                photo_id = self.upload_media(image_path)
                if not photo_id:
                    logger.warning(f"[{self.name}] Posting without image (failed upload)")
                    payload = {"message": message, "access_token": self.access_token}
                else:
                    payload = {
                        "message": message,
                        "attached_media": json.dumps([{"media_fbid": photo_id}]),
                        "access_token": self.access_token,
                    }
                url = f"{self.graph_url}/feed"
            else:
                # Just a text post
                payload = {"message": message, "access_token": self.access_token}
                url = f"{self.graph_url}/feed"

            response = requests.post(url, data=payload)
            result = response.json()
            if response.status_code != 200:
                logger.error(f"[{self.name}] Failed to post to Facebook: {result}")
                return

            self.message_cache.add(MessageCacheRecord(message=cache_key))
            logger.info(f"[{self.name}] Posted {cache_key}")

        except Exception as e:
            logger.exception(f"[{self.name}] Unexpected error posting to Facebook: {e}")

    def upload_media(self, image_path: Path) -> str | None:
        """
        Upload a photo to Facebook and return the media ID.
        Uses media_cache to avoid re-uploading the same file.
        """
        # Check cache first
        cached = self.media_cache.get(image_path)
        if cached:
            logger.info(f"[{self.name}] Using cached media_id for {image_path}")
            return cached.media_id

        if not image_path.exists():
            logger.warning(f"[{self.name}] Cannot upload media; file does not exist: {image_path}")
            return None

        try:
            url = f"{self.graph_url}/photos"
            files = {"source": open(image_path, "rb")}
            payload = {
                "published": False,
                "access_token": self.access_token,
            }  # unpublished to attach later
            response = requests.post(url, files=files, data=payload)
            files["source"].close()
            result = response.json()

            if "identifier" not in result:
                logger.error(f"[{self.name}] Failed to upload media {image_path}: {result}")
                return None

            media_id = result["identifier"]
            self.media_cache.add(MediaCacheRecord(filename=str(image_path), media_id=media_id))
            logger.info(f"[{self.name}] Uploaded media {image_path} -> media_id={media_id}")
            return media_id

        except Exception as e:
            logger.exception(f"[{self.name}] Unexpected error uploading media {image_path}: {e}")
            return None
