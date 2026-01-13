import logging

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from crimereporter.caches.text import TextCache, TextCacheRecord
from crimereporter.utils.config import Config
from crimereporter.youtube.commands import YoutubeCommand

logger = logging.getLogger(__name__)
call_logger = logging.getLogger("call.logger.youtube")

config = Config()

texts_cache = TextCache()


class UploadCaptionsYoutubeCommand(YoutubeCommand):
    """Upload captions for the video."""

    def run(self) -> None:
        if not self.video_id:
            logger.warning("Video not found for title: %s", self.title)
            return

        if not self.text_file.exists():
            logger.warning("Caption file not found: %s", self.text_file)
            return

        # Check cache for existing caption hash
        cached_record = texts_cache.get(self.video_id)
        if cached_record and cached_record.text_hash == self.text_hash:
            logger.info("Skipping captions upload for %s (no change detected)", self.title)
            return

        try:
            call_logger.info(f"Get captions     {self.title}")
            captions_api = self.youtube.captions()
            existing_captions = captions_api.list(part="snippet", videoId=self.video_id).execute().get("items", [])

            caption_id_to_update = None
            for cap in existing_captions:
                snippet = cap["snippet"]
                if snippet["language"] == "en" and snippet["name"] == "Transcript":
                    caption_id_to_update = cap["id"]
                    break

            media = MediaFileUpload(str(self.text_file), mimetype="text/plain")
            if caption_id_to_update:
                call_logger.info(f"Update captions  {self.title}")
                captions_api.update(
                    part="snippet",
                    body={
                        "id": caption_id_to_update,
                        "snippet": {
                            "videoId": self.video_id,
                            "language": "en",
                            "name": "Transcript",
                        },
                    },
                    media_body=media,
                ).execute()
                logger.info("Captions replaced for video ID: %s", self.video_id)
            else:
                call_logger.info(f"Insert captions  {self.title}")
                captions_api.insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "videoId": self.video_id,
                            "language": "en",
                            "name": "Transcript",
                            "isDraft": False,
                        }
                    },
                    media_body=media,
                ).execute()
                logger.info("Captions uploaded for video ID: %s", self.video_id)

            # Update cache with new hash
            texts_cache.add(TextCacheRecord(video_id=self.video_id, text_hash=self.text_hash))
            logger.info("Woken up")

        except HttpError as e:
            if e.resp.status == 429:
                logger.error(
                    "Rate limit exceeded when uploading captions for video ID %s",
                    self.video_id,
                )
            else:
                logger.error("HttpError while uploading captions: %s", e)
            raise
        except Exception as e:
            logger.exception("Unexpected error while uploading captions: %s", e)
            raise
