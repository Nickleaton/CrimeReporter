import pickle
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from crimereporter.utils.config import Config

# Your YouTube API scope
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

config = Config()


class YouTubeClient:
    """Independent YouTube API client for video and metadata management."""

    def __init__(
        self,
        secrets_file: Path,
        token_file: Path = Path(config.root) / "keys/token.pkl",
    ) -> None:
        self.secrets_file = secrets_file
        self.token_file = token_file
        self.service = self.build_service()

    # -----------------------------------------------------
    # Auth / Credentials
    # -----------------------------------------------------
    def get_credentials(self) -> Credentials:
        """Load or refresh YouTube API credentials."""
        creds: Optional[Credentials] = None

        if self.token_file.exists():
            with self.token_file.open("rb") as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(self.secrets_file), SCOPES)
                creds = flow.run_local_server(port=0)
            with self.token_file.open("wb") as f:
                pickle.dump(creds, f)
        return creds

    def build_service(self):
        """Create YouTube service client."""
        creds = self.get_credentials()
        return build("youtube", "v3", credentials=creds)

    # -----------------------------------------------------
    # Video listing / metadata
    # -----------------------------------------------------
    def get_all_videos(self) -> list[tuple[str, str]]:
        """Return a list of (video_id, title) for all videos on the authenticated channel."""
        videos: list[tuple[str, str]] = []

        # Step 1: Get channel uploads playlist
        channel_response = self.service.channels().list(part="contentDetails", mine=True).execute()

        uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        # Step 2: Paginate through playlist items
        next_page_token = None
        while True:
            playlist_response = (
                self.service.playlistItems()
                .list(
                    part="snippet",
                    playlistId=uploads_playlist_id,
                    maxResults=50,
                    pageToken=next_page_token,
                )
                .execute()
            )

            for item in playlist_response.get("items", []):
                snippet = item["snippet"]
                video_id = snippet["resourceId"]["videoId"]
                title = snippet["title"]
                videos.append((video_id, title))

            next_page_token = playlist_response.get("nextPageToken")
            if not next_page_token:
                break

        return videos

    def get_all_playlists(self) -> list[tuple[str, str]]:
        """
        Return a list of (playlist_id, title) for all playlists
        on the authenticated channel.
        """
        playlists: list[tuple[str, str]] = []
        next_page_token = None

        while True:
            response = (
                self.service.playlists()
                .list(part="snippet", mine=True, maxResults=50, pageToken=next_page_token)
                .execute()
            )

            for item in response.get("items", []):
                playlist_id = item["id"]
                title = item["snippet"]["title"]
                playlists.append((playlist_id, title))

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        return playlists

    def get_videos_by_playlist(self) -> list[tuple[str, str, str]]:
        """
        Return a list of tuples: (playlist_name, video_title, video_id)
        for all videos in all playlists on the authenticated channel.
        """
        videos_by_playlist: list[tuple[str, str, str]] = []

        # First, get all playlists
        playlists = self.get_all_playlists()

        for playlist_id, playlist_name in playlists:
            next_page_token = None
            while True:
                response = (
                    self.service.playlistItems()
                    .list(
                        part="snippet",
                        playlistId=playlist_id,
                        maxResults=50,
                        pageToken=next_page_token,
                    )
                    .execute()
                )

                for item in response.get("items", []):
                    snippet = item["snippet"]
                    video_id = snippet["resourceId"]["videoId"]
                    video_title = snippet["title"]
                    videos_by_playlist.append((playlist_name, video_title, video_id))

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

        return videos_by_playlist
