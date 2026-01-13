import csv
from pathlib import Path

import yaml

AVOID = ["00120"]
# Base directory to start searching
base_dir = Path("programs")

cfile = Path("caches/ident_title.csv")
# List to store all found YAML file paths
yaml_files = []

# Recursively search for all 'script.yaml' files
for yaml_file in base_dir.rglob("script.yaml"):
    yaml_files.append(yaml_file)

print(f"Found {len(yaml_files)} YAML files.")

# Optional: iterate and load YAML content
with cfile.open("w", newline="", encoding="utf-8") as wf:
    writer = csv.writer(wf)
    writer.writerow(["ident", "title"])
    for file_path in yaml_files:
        ident = file_path.parent.name
        if ident in AVOID:
            continue
        with file_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        title = f"{data['Date']}: {data['Title']}"
        writer.writerow([ident, title])
