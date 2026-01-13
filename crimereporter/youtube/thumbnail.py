import logging

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from crimereporter.caches.thumbnail import ThumbnailCache, ThumbnailCacheRecord
from crimereporter.youtube.commands import YoutubeCommand

logger = logging.getLogger(__name__)
call_logger = logging.getLogger("call.logger.youtube")

thumbnails_cache = ThumbnailCache()


class UploadThumbnailYoutubeCommand(YoutubeCommand):
    """Upload a thumbnail for the video."""

    def run(self) -> None:
        if not self.video_id:
            logger.warning("Video not found for title: %s", self.title)
            return

        if not self.thumbnail_file.exists():
            logger.warning("Thumbnail file not found: %s", self.thumbnail_file)
            return

        # Check cache for existing thumbnail hash
        cached_record = thumbnails_cache.get(self.video_id)
        if cached_record and cached_record.thumbnail_hash == self.thumbnail_hash:
            logger.info("Skipping thumbnail upload for %s (no change detected)", self.title)
            return

        call_logger.info(f"Upload thumbnail {self.title}")
        try:
            self.youtube.thumbnails().set(
                videoId=self.video_id,
                media_body=MediaFileUpload(str(self.thumbnail_file)),
            ).execute()
            logger.info("Thumbnail uploaded for video ID: %s", self.video_id)

            # Update cache with new hash
            thumbnails_cache.add(ThumbnailCacheRecord(video_id=self.video_id, thumbnail_hash=self.thumbnail_hash))

        except HttpError as e:
            if e.resp.status == 429:
                logger.error(
                    "Rate limit exceeded when uploading thumbnail for video ID %s",
                    self.video_id,
                )
            else:
                logger.error("HttpError while uploading thumbnail: %s", e)
        except Exception as e:
            logger.exception("Unexpected error while uploading thumbnail: %s", e)
