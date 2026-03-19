# Cache Migration Plan: CSV → PostgreSQL

## Overview

All caches currently use CSV files as backing storage, managed via `BaseCache` and `CSVCache`.
The goal is to migrate each cache to PostgreSQL using SQLAlchemy, running CSV and DB in parallel
during the cutover period before removing the CSV layer entirely.

The singleton pattern used by some caches is load-bearing under the current single-process model
but becomes redundant (and unsafe) under parallel workers — the DB naturally replaces it.

---

## Architecture

### New layers

```
BaseCache (unchanged interface)
    └── CSVCache (extended during cutover to also write to DB)
```~~~~

No wrapper class needed. DB writes are added directly into `CSVCache`. When cutover is complete,
the CSV code is deleted and what remains is pure DB.

### Shared infrastructure

- `crimereporter/db/models.py` — SQLAlchemy ORM models (one per cache type)
- `crimereporter/db/session.py` — shared engine and `SessionFactory`
- `alembic/` — migration scripts managed by Alembic

### Alembic setup

Alembic is configured from the start so schema changes are tracked from day one.
The first migration is simply the initial table creation.

**Directory structure:**
```
alembic/
    env.py
    script.py.mako
    versions/
        0001_initial_schema.py
alembic.ini
```

**`alembic.ini`** points at the DB URL from config:
```ini
sqlalchemy.url = postgresql://user:pass@localhost/crimereporter
```

**`env.py`** imports `Base` from `crimereporter/db/models.py` so Alembic can autogenerate
migrations by diffing the ORM models against the live schema:
```python
from crimereporter.db.models import Base
target_metadata = Base.metadata
```

**Workflow for schema changes:**
```bash
# Generate a new migration from model changes
alembic revision --autogenerate -m "add ollama_status to cache"

# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1
```

**Initial migration** (`0001_initial_schema.py`) is generated once all models are defined:
```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

Autogenerate handles column additions, removals, and type changes. It does not detect
changes to indexes or constraints automatically — those must be added manually to the
migration script when needed.

---

## Migration Order

### Priority 1 — `Cache` (article cache)

Most critical: in the hot path of every worker, currently a singleton with concurrent write risk.

**Record:** `CacheRecord`

| Field | Type | Notes |
|---|---|---|
| `url` | `String` | Primary key |
| `date` | `String` | |
| `title` | `String` | |
| `source_name` | `String` | |
| `filename` | `String` | Stored as POSIX path |
| `timestamp` | `TIMESTAMP` | Used for date filtering in `records()` |

**Key changes:**
- `is_cached()` becomes a `SELECT` by primary key
- `add()` becomes a Postgres `INSERT ... ON CONFLICT DO UPDATE`
- `records()` moves date filtering from Python into a `WHERE` clause — performance win as cache grows
- `@singleton` can be dropped once DB-backed; no in-memory state to protect

---

### Priority 2 — `AudioCache`

Most complex record shape. Composite key derived from a `@property`, nullable fields, non-string types.

**Record:** `AudioCacheRecord`

| Field | Type | Notes |
|---|---|---|
| `renderer` | `String` | Part of composite key |
| `text_hash` | `String` | Part of composite key |
| `language` | `String` | Nullable |
| `voice` | `String` | Nullable |
| `file_path` | `String` | Default `""` |
| `size` | `Integer` | Default `0` |
| `text` | `String` | Default `""` |

**Composite key:** `renderer:language:voice:text_hash` — stored as a generated/computed column
or derived in the `SQLAlchemyCache` layer using `key_field="composite_key"` (already works via
`@property` and `getattr`).

---

### Priority 3 — `MessageCache` (poster idempotency guard)

`MessageCache` is the idempotency guard that prevents double-posting to live platforms — losing
it means duplicate posts. It is a record cache and backfill is essential.

Each poster has its own message cache, currently scoped by filename. In the DB this becomes a
`platform` column derived from `Poster.name` (`X`, `Bluesky`, etc.).

**Record:** `MessageCacheRecord`

| Field | Type | Notes |
|---|---|---|
| `platform` | `String` | Part of composite PK |
| `video_id` | `String` | Part of composite PK |
| `video_title` | `String` | |
| `message` | `String` | |

**Key change:** No `load_cache()` needed — idempotency is checked at runtime directly against
the DB. No in-memory state required.

`Poster.__init__` passes `self.name` instead of a file path:

```python
self.message_cache = MessageCache(platform=self.name)
```

**Note:** `BlueskyPoster` currently overwrites `self.message_cache` after `super().__init__()`
with an identical path — this is redundant and should be removed.

---

### Priority 4 — `MediaCache` (poster media upload cache)

Scoped per platform like `MessageCache`. Lookup cache — an empty DB means a redundant re-upload,
not a duplicate post.

**Record:** `MediaCacheRecord`

| Field | Type | Notes |
|---|---|---|
| `platform` | `String` | Part of composite PK |
| `filename` | `String` | Part of composite PK |
| `media_id` | `String` | |

**Open issue:** `BlueskyPoster` stores a `BlobRef` object as `media_id` rather than a string.
This must be normalised to a string before it can be stored in the DB column.

---

### Priority 5 — YouTube caches (batch)

All share the same two-field string pair shape. Can be migrated in one pass.

| Cache | Key field | Value field |
|---|---|---|
| `TitleCache` | `title` | `video_id` |
| `ThumbnailCache` | `thumbnail_hash` | `video_id` |
| `TextCache` | `video_id` | `text_hash` |
| `PlaylistVideoCache` | `list` | `title` |
| `MetadataCache` | `video_id` | `metadata_hash` |

---

## Cache Categories

| Cache | Type | Backfill needed | Notes |
|---|---|---|---|
| `Cache` (article) | Record | No | Handled separately outside this migration |
| `MessageCache` | Record | No | Starts fresh — worst case is a re-post of recent items |
| `TitleCache` | Record | No | Starts empty, populated manually at a later date |
| `PlaylistVideoCache` | Record | Yes — by hand | Must be populated before reads flip to DB |
| `AudioCache` | Lookup | No | Rebuilds naturally — slow but not wrong |
| `ThumbnailCache` | Lookup | No | Rebuilds naturally |
| `TextCache` | Lookup | No | Rebuilds naturally |
| `MetadataCache` | Lookup | No | Rebuilds naturally |
| `MediaCache` | Lookup | No | Re-upload cost only |

No automated backfill script required. `PlaylistVideoCache` is the only cache that needs
manual population before reads can be safely flipped to the DB.

---

## Cutover Strategy

Each cache follows the same four-phase process:

### Phase 0 — Seed data

Insert the 5 `PlaylistVideoCache` rows directly into the DB before going live. All other
caches start fresh or rebuild naturally.

### Phase 1 — Dual write (inline)

DB writes are added directly into `CSVCache.add()`. No wrapper class needed.
`is_cached()` cross-checks both and logs an error if they disagree — CSV remains
source of truth, workers keep running.

```python
def add(self, record: T, *extra_key_parts: str) -> None:
    # existing CSV logic unchanged
    ...
    self._add_to_db(record)

def is_cached(self, url: str) -> bool:
    in_csv = url in self.cache
    in_db = self._is_cached_db(url)
    if in_csv != in_db:
        logger.error(f"Cache mismatch for {url}: csv={in_csv} db={in_db}")
    return in_csv  # CSV is source of truth until cutover
```

### Phase 2 — Validate

Monitor error logs for mismatches. Compare record counts between CSV and DB.
When satisfied, flip `is_cached()` to read from DB:

```python
def is_cached(self, url: str) -> bool:
    in_csv = url in self.cache
    in_db = self._is_cached_db(url)
    if in_csv != in_db:
        logger.error(f"Cache mismatch for {url}: csv={in_csv} db={in_db}")
    return in_db  # DB is now source of truth
```

### Phase 3 — Cut over

- Delete all CSV read/write code from `CSVCache`
- Delete CSV files
- Remove `is_cached` cross-check logging

---

## Composite Key Note

`BaseCache` already supports composite keys via `key_field="composite_key"` and `@property`.
This works unchanged in the SQLAlchemy layer — `getattr(record, self.key_field)` resolves the
property. No special casing needed in the base.

The `extra_key_parts` argument in `BaseCache.add()` appears unused across all current cache types
and should be reviewed for removal before the migration to avoid carrying dead code into the new layer.

---

## Concurrency Considerations

Parallel workers are not introduced until the DB migration is complete — by that point CSV
will already be gone, so CSV concurrency risks are not a concern.

Once workers are running against the DB:
- `is_cached()` is a transactional DB read — safe under concurrency
- `add()` uses `INSERT ... ON CONFLICT DO UPDATE` — idempotent under concurrent writes
- The cache check should live in `FetchArticleCommand.execute()` (worker side) rather than
  at enqueue time, to close the race where two workers pick up the same URL before either
  has written to the cache

---

## Open Questions

- `MediaCacheRecord.media_id` stores a `BlobRef` object in `BlueskyPoster` rather than a string.
  This must be normalised before DB storage — confirm serialisation format (e.g. `str(blob_ref)`
  or a JSON representation).
- Is `extra_key_parts` in `BaseCache.add()` used anywhere outside the codebase shown? If not, remove
  before migrating to avoid carrying dead code into the SQLAlchemy layer.