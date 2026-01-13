# Write to CSV
import csv
from pathlib import Path

from crimereporter.youtube.client import YouTubeClient

yt = YouTubeClient(secrets_file=Path("keys/youtube_secrets.json"))
videos_by_playlist = yt.get_videos_by_playlist()


output_file = Path("caches/youtube_videos_by_playlist.csv")
with output_file.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["playlist_name", "video_title", "video_id"])
    for playlist_name, video_title, video_id in videos_by_playlist:
        writer.writerow([playlist_name, video_title, video_id])

print(f"✅ Wrote {len(videos_by_playlist)} videos to {output_file.resolve()}")
