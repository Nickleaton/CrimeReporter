import logging

from googleapiclient.errors import HttpError

from crimereporter.caches.metadata import MetadataCache, MetadataCacheRecord
from crimereporter.youtube.commands import YoutubeCommand

logger = logging.getLogger(__name__)
call_logger = logging.getLogger("call.logger.youtube")

metadata_cache = MetadataCache()


class UpdateVideoMetadataCommand(YoutubeCommand):
    """Update metadata for the video."""

    def run(self) -> None:
        if not self.video_id:
            logger.warning("Video not found for title: %s", self.title)
            return

        # Check cache for existing metadata hash
        cached_record = metadata_cache.get(self.video_id)
        if cached_record and cached_record.metadata_hash == self.metadata_hash:
            logger.info("Skipping metadata update for %s (no change detected)", self.title)
            return

        try:
            call_logger.info(f"Update metadata  {self.title}")
            self.youtube.videos().update(part="snippet,status", body=self.create_metadata()).execute()
            logger.info("Updated metadata for video ID: %s", self.video_id)

            # Update cache with new hash
            metadata_cache.add(MetadataCacheRecord(video_id=self.video_id, metadata_hash=self.metadata_hash))

        except HttpError as e:
            if e.resp.status == 429:
                logger.error(
                    "Rate limit exceeded when updating metadata for video ID %s",
                    self.video_id,
                )
            else:
                logger.error("HttpError while updating metadata: %s", e)
            raise
        except Exception as e:
            logger.exception("Unexpected error while updating metadata: %s", e)
            raise
