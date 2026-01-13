import logging
import time
from pathlib import Path

import tweepy
import yaml

from crimereporter.caches.media_cache import MediaCacheRecord
from crimereporter.caches.message_cache import MessageCacheRecord
from crimereporter.posters.poster import Poster
from crimereporter.utils.config import Config

logger = logging.getLogger(__name__)

config = Config()


class XPoster(Poster):
    """Poster implementation for posting to X (Twitter) with optional media."""

    def __init__(self):
        super().__init__()
        creds_path = Path(config.keys_directory) / Path("x.yaml")
        creds = yaml.safe_load(creds_path.read_text(encoding="utf-8"))

        required = {
            "consumer_key",
            "consumer_secret",
            "access_token",
            "access_token_secret",
        }
        missing = required - creds.keys()
        if missing:
            logger.fatal(f"Missing X API credentials: {missing}")
            raise RuntimeError(f"Missing X API credentials: {missing}")

        # v1.1 API for media uploads
        auth = tweepy.OAuth1UserHandler(
            creds["consumer_key"],
            creds["consumer_secret"],
            creds["access_token"],
            creds["access_token_secret"],
        )
        self.api_v1 = tweepy.API(auth)

        # v2 API for posting tweets
        self.api_v2 = tweepy.Client(
            consumer_key=creds["consumer_key"],
            consumer_secret=creds["consumer_secret"],
            access_token=creds["access_token"],
            access_token_secret=creds["access_token_secret"],
        )

    def post_message(
        self,
        video_id: str,
        video_title: str,
        message: str,
        image_path: Path | None = None,
    ):
        """
        Post a message with optional media to X.
        Idempotency is enforced per video using video_id in the message cache.
        """
        if self.message_cache.get(video_id):
            logger.info(f"[{self.name}] Skipping video {video_id} (already posted)")
            return

        media_ids = None
        if image_path:
            if image_path.exists():
                media_id = self.upload_media(image_path)
                if media_id:
                    media_ids = [media_id]
            else:
                logger.warning(f"[{self.name}] Image path {image_path} does not exist. Posting without media.")

        try:
            self.api_v2.create_tweet(text=message, media_ids=media_ids)
        except tweepy.errors.TooManyRequests as e:
            self.log_rate_limit(e, context="posting tweet")
            return
        except tweepy.errors.Unauthorized:
            logger.error(f"[{self.name}] Unauthorized: Check your API credentials and permissions")
            return
        except tweepy.TweepyException as e:
            logger.error(f"[{self.name}] Failed to post tweet: {e}")
            self.log_response_details(e)
            return

        self.message_cache.add(MessageCacheRecord(video_id=video_id, video_title=video_title, message=message))
        logger.info(f"[{self.name}] Posted video {video_id}")

    def upload_media(self, image_path: Path) -> str | None:
        """
        Upload media to X and return the media ID.
        Uses media_cache to avoid re-uploading the same file.
        """
        cached = self.media_cache.get(image_path)
        if cached:
            logger.info(f"[{self.name}] Using cached media_id")
            return cached.media_id

        if not image_path.exists():
            logger.warning(f"[{self.name}] Cannot upload media; file does not exist: {image_path}")
            return None

        try:
            media = self.api_v1.media_upload(str(image_path))
            media_id = str(media.media_id)

            self.media_cache.add(MediaCacheRecord(filename=str(image_path), media_id=media_id))
            logger.info(f"[{self.name}] Uploaded media")
            return media_id

        except tweepy.errors.TooManyRequests as e:
            self.log_rate_limit(e, context=f"uploading media ({image_path})")
        except tweepy.errors.Unauthorized:
            logger.error(f"[{self.name}] Unauthorized: Check your API credentials and permissions")
        except tweepy.TweepyException as e:
            logger.error(f"[{self.name}] Failed to upload media {image_path}: {e}")
            self.log_response_details(e)
        except Exception as e:
            logger.exception(f"[{self.name}] Unexpected error uploading media {image_path}: {e}")

        return None

    def log_rate_limit(self, e: tweepy.errors.TooManyRequests, context: str):
        """Log detailed rate-limit info from a TooManyRequests error."""
        response = getattr(e, "response", None)
        if response is None:
            logger.error(f"[{self.name}] Rate limit hit while {context}, but no response object available: {e}")
            return

        headers = response.headers
        limit = headers.get("x-rate-limit-limit")
        remaining = headers.get("x-rate-limit-remaining")
        reset = headers.get("x-rate-limit-reset")

        reset_human = None
        if reset:
            try:
                reset_human = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(reset)))
            except ValueError:
                reset_human = str(reset)

        logger.error(
            f"[{self.name}] Rate limit hit while {context}: "
            f"limit={limit}, remaining={remaining}, reset={reset_human}"
        )

    def log_response_details(self, e: tweepy.TweepyException):
        """Log Tweepy response details for debugging."""
        response = getattr(e, "response", None)
        if response:
            logger.info(f"[{self.name}] Response status: {response.status_code}")
            logger.info(f"[{self.name}] Headers: {dict(response.headers)}")
            logger.info(f"[{self.name}] Body: {response.text}")
