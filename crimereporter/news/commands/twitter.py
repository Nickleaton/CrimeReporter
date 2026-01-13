from pathlib import Path

import requests
from requests_oauthlib import OAuth1

from crimereporter.news.commands.commands import logger
from crimereporter.news.commands.composed import ComposedCommand
from crimereporter.news.commands.simple import SimpleCommand
from crimereporter.utils.format import Format


class XAuth:
    """Helper for OAuth1 signing."""

    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret):
        self.auth = OAuth1(consumer_key, consumer_secret, access_token, access_token_secret)


class UploadVideoXCommand(SimpleCommand):
    """Upload video to X (Twitter)."""

    def __init__(self, input_file, fmt: Format, auth: XAuth):
        super().__init__(input_file, fmt)
        self.auth = auth.auth
        self.video_file = self.input_file.parent / "output" / f"{self.format.name}.mp4"
        self.media_id = None

    def execute(self) -> None:
        super().execute()

        file_path = Path(self.video_file)
        total_bytes = file_path.stat().st_size

        # INIT
        init_req = requests.post(
            "https://upload.twitter.com/1.1/media/upload.json",
            data={
                "command": "INIT",
                "media_type": "video/mp4",
                "total_bytes": total_bytes,
            },
            auth=self.auth,
        )
        init_resp = init_req.json()
        self.media_id = init_resp["media_id"]

        # APPEND (5MB chunks)
        segment_id = 0
        with file_path.open("rb") as f:
            while chunk := f.read(5 * 1024 * 1024):
                requests.post(
                    "https://upload.twitter.com/1.1/media/upload.json",
                    data={
                        "command": "APPEND",
                        "media_id": self.media_id,
                        "segment_index": segment_id,
                    },
                    files={"media": chunk},
                    auth=self.auth,
                )
                segment_id += 1

        # FINALIZE
        requests.post(
            "https://upload.twitter.com/1.1/media/upload.json",
            data={"command": "FINALIZE", "media_id": self.media_id},
            auth=self.auth,
        )

        logger.info("Video uploaded to X with media_id=%s", self.media_id)


class PostTweetXCommand(SimpleCommand):
    """Post a tweet with uploaded video."""

    def __init__(self, input_file, fmt: Format, auth: XAuth, media_id: str, text: str):
        super().__init__(input_file, fmt)
        self.auth = auth.auth
        self.media_id = media_id
        self.text = text

    def execute(self) -> None:
        super().execute()

        url = "https://api.twitter.com/2/tweets"
        payload = {
            "text": self.text,
            "media": {"media_ids": [self.media_id]},
        }
        resp = requests.post(url, json=payload, auth=self.auth)

        if resp.status_code == 201:
            tweet_id = resp.json()["data"]["identifier"]
            logger.info("Tweet posted successfully: https://x.com/i/web/status/%s", tweet_id)
        else:
            logger.error("Failed to post tweet: %s", resp.text)


class XCommand(ComposedCommand):
    """Combined command for uploading + tweeting video."""

    def __init__(self, input_file, fmt: Format, auth: XAuth, text: str):
        upload_cmd = UploadVideoXCommand(input_file, fmt, auth)
        post_cmd = PostTweetXCommand(input_file, fmt, auth, upload_cmd.media_id, text)
        super().__init__([upload_cmd, post_cmd])
