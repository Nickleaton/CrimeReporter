import csv
from pathlib import Path

from crimereporter.youtube.client import YouTubeClient

# Initialize client
yt = YouTubeClient(secrets_file=Path("keys/youtube_secrets.json"))

# Fetch all videos
videos = yt.get_all_videos()

# Output CSV file
output_file = Path(r"caches\youtube_title_to_id_2.csv")

# Write CSV with header
with output_file.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["title", "video_id"])  # header row
    for vid, title in videos:
        writer.writerow([title, vid])

print(f"✅ Wrote {len(videos)} videos to {output_file.resolve()}")
