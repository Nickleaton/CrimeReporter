import logging
from pathlib import Path

from googleapiclient.errors import HttpError

from crimereporter.caches.playlist_cache import PlaylistCache
from crimereporter.utils.config import Config
from crimereporter.youtube.commands import YoutubeCommand

logger = logging.getLogger(__name__)
call_logger = logging.getLogger("call.logger.youtube")

config = Config()
playlist_cache = PlaylistCache(Path(config.caches) / Path("playlist_cache.csv"))


class UpdatePlaylistCommand(YoutubeCommand):
    """Add a video to a YouTube playlist."""

    def run(self) -> None:
        playlist_name = self.script.parsed.get("Type")
        if not playlist_name:
            logger.warning("No playlist type specified for video: %s", self.title)
            return

        # Look up the playlist in the cache
        record = playlist_cache.get(playlist_name)
        if not record:
            logger.warning('Playlist "%s" not found in cache', playlist_name)
            return

        playlist_id = record.id
        logger.info(
            'Adding video %s to playlist "%s" (%s)',
            self.video_id,
            playlist_name,
            playlist_id,
        )

        try:
            call_logger.info(f"Add to Playlist {playlist_name}")
            self.youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": self.video_id,
                        },
                    },
                },
            ).execute()
            logger.info("Video %s added to playlist %s", self.video_id, playlist_name)
        except HttpError as e:
            if e.resp.status == 409:  # already in playlist
                logger.warning("Video %s already in playlist %s", self.video_id, playlist_name)
            elif e.resp.status == 403:
                logger.error(
                    "Insufficient permissions to add video to playlist %s",
                    playlist_name,
                )
            elif e.resp.status == 404:
                logger.error("Playlist not found: %s", playlist_id)
            else:
                logger.error("HttpError while adding video to playlist: %s", e)
            raise
        except Exception as e:
            logger.exception("Unexpected error while adding video to playlist: %s", e)
            raise
