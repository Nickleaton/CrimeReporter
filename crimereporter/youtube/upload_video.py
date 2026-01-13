import logging
import time

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from crimereporter.caches.title import TitleCache, TitleCacheRecord
from crimereporter.utils.config import Config
from crimereporter.youtube.commands import YoutubeCommand

logger = logging.getLogger(__name__)
call_logger = logging.getLogger("call.logger.youtube")

titles_cache = TitleCache()

config = Config()


class UploadVideoYoutubeCommand(YoutubeCommand):
    """Upload a video file to YouTube."""

    def run(self) -> None:
        if self.video_id:
            logger.warning("Video already exists for title: %s", self.title)
            return

        try:
            call_logger.info(f"Upload video     {self.title}")
            request = self.youtube.videos().insert(
                part="snippet,status",
                body=self.create_metadata(),
                media_body=MediaFileUpload(str(self.video_file)),
            )
            response = request.execute()
            self.video_id = response["id"]
            record = TitleCacheRecord(title=self.title, video_id=self.video_id)
            titles_cache.add(record)
            logger.info("Uploaded video ID: %s", self.video_id)
            logger.info(f"Sleeping for {config.youtube.sleep_after_upload} seconds")
            time.sleep(config.youtube.sleep_after_upload)
            logger.info("Woken up")
        except HttpError as e:
            if e.resp.status == 429:
                logger.error("Rate limit exceeded when uploading video: %s", self.title)
            else:
                logger.error("HttpError while uploading video: %s", e)
            raise
        except Exception as e:
            logger.exception("Unexpected error while uploading video: %s", e)
            raise
