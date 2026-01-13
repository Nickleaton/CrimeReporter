import logging
from pathlib import Path

from crimereporter.youtube.captions import UploadCaptionsYoutubeCommand
from crimereporter.youtube.commands import YoutubeCommand
from crimereporter.youtube.metadata import UpdateVideoMetadataCommand
from crimereporter.youtube.playlist import UpdatePlaylistCommand
from crimereporter.youtube.thumbnail import UploadThumbnailYoutubeCommand
from crimereporter.youtube.upload_video import UploadVideoYoutubeCommand

logger = logging.getLogger(__name__)


class YoutubeComposedCommand(YoutubeCommand):
    """Full workflow: upload video, thumbnail, captions, and metadata."""

    def __init__(self, input_file: Path, orientation: str) -> None:
        super().__init__(input_file, orientation)
        self.upload_video_cmd = UploadVideoYoutubeCommand(input_file, orientation)
        self.upload_thumbnail_cmd = UploadThumbnailYoutubeCommand(input_file, orientation)
        self.upload_captions_cmd = UploadCaptionsYoutubeCommand(input_file, orientation)
        self.update_metadata_cmd = UpdateVideoMetadataCommand(input_file, orientation)
        self.update_playlist_cmd = UpdatePlaylistCommand(input_file, orientation)

    def run(self) -> None:
        logger.info("Starting YouTube workflow for %s", self.title)

        # Step 1: Upload video
        self.upload_video_cmd.run()

        # Step 2: Propagate video_id to dependent commands
        video_id = self.upload_video_cmd.video_id
        if not video_id:
            logger.error("Workflow aborted: video upload failed.")
            return

        self.upload_thumbnail_cmd.video_id = video_id
        self.upload_captions_cmd.video_id = video_id
        self.update_metadata_cmd.video_id = video_id
        self.update_playlist_cmd.video_id = video_id

        # Step 3: Run dependent commands
        self.upload_thumbnail_cmd.run()
        self.upload_captions_cmd.run()
        self.update_metadata_cmd.run()
        self.update_playlist_cmd.run()

        logger.info("Finished YouTube workflow for %s", self.title)
