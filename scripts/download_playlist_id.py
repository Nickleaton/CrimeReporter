import csv
from pathlib import Path

from crimereporter.youtube.client import YouTubeClient

# Initialize client
yt = YouTubeClient(secrets_file=Path("keys/youtube_secrets.json"))

# Fetch all playlists
playlists = yt.get_all_playlists()

# Output CSV file
output_file = Path(r"caches\youtube_playlists_2.csv")

# Write CSV with header
with output_file.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["name", "id"])  # header row
    for vid, title in playlists:
        writer.writerow([title, vid])

print(f"✅ Wrote {len(playlists)} playlists to {output_file.resolve()}")
