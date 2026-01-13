import logging

logger = logging.getLogger(__name__)


# class BaseCache:
#     """CSV-backed key-value cache with headers."""
#
#     def __init__(self, csv_file: Path, headers: list[str] | None = None) -> None:
#         self.csv_file = csv_file
#         self.headers = headers if headers is not None else ['key', 'value']
#         self.cache: dict[str, str] = {}
#
#         self.csv_file.parent.mkdir(parents=True, exist_ok=True)
#         self._load()
#
#     def _load(self) -> None:
#         if not self.csv_file.exists():
#             return
#         try:
#             with self.csv_file.open(newline='', encoding='utf-8') as f:
#                 reader = csv.reader(f)
#                 first_row = True
#                 for row in reader:
#                     if first_row:
#                         # Skip header row
#                         first_row = False
#                         continue
#                     if len(row) == 2:
#                         k, v = row
#                         self.cache[k] = v
#                     else:
#                         logger.warning(f'Skipping malformed row in {self.csv_file}: {row}')
#         except (OSError, csv.Error) as e:
#             logger.warning(f'Failed to load cache from {self.csv_file}: {e}')
#
#     def get(self, key: str) -> Optional[str]:
#         return self.cache.get(key)
#
#     def add(self, key: str, value: str) -> None:
#         if self.cache.get(key) == value:
#             return
#         self.cache[key] = value
#         self._persist()
#
#     def _persist(self) -> None:
#         temp_file = self.csv_file.with_suffix('.tmp')
#         try:
#             with temp_file.open(mode='w', newline='', encoding='utf-8') as f:
#                 writer = csv.writer(f)
#                 # Write headers first
#                 writer.writerow(self.headers)
#                 for k, v in self.cache.items():
#                     writer.writerow([k, v])
#             temp_file.replace(self.csv_file)
#         except OSError as e:
#             logger.error(f'Failed to write cache file {self.csv_file}: {e}')
#
#     def clear(self) -> None:
#         self.cache.clear()
#         try:
#             if self.csv_file.exists():
#                 self.csv_file.unlink()
#         except OSError as e:
#             logger.warning(f'Failed to delete cache file {self.csv_file}: {e}')
#
#     def __len__(self) -> int:
#         return len(self.cache)
#
#     def __contains__(self, key: str) -> bool:
#         return key in self.cache

#
# @singleton
# class TitleCache(BaseCache):
#     """Cache mapping title → video_id."""
#
#     def __init__(self) -> None:
#         super().__init__(Path('caches/youtube_title_to_id.csv'), ['title', 'video_id'])

#
# @singleton
# class ThumbnailCache(BaseCache):
#     """Cache mapping video_id → thumbnail_hash."""
#
#     def __init__(self) -> None:
#         super().__init__(Path('caches/youtube_thumbnail.csv'), ['video_id', 'thumbnail_hash'])
#

# @singleton
# class TextCache(BaseCache):
#     """Cache mapping video_id → text_hash."""
#
#     def __init__(self) -> None:
#         super().__init__(Path('caches/youtube_text.csv'), ['video_id', 'text_hash'])

#
# @singleton
# class MetadataCache(BaseCache):
#     """Cache mapping video_id → metadata_hash."""
#
#     def __init__(self) -> None:
#         super().__init__(Path('caches/youtube_metadata.csv'), ['video_id', 'metadata_hash'])
