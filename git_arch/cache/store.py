from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from git_arch import __version__


def make_cache_key(
    blob_hash: str,
    analyzer_id: str,
    config_fingerprint: str,
    extra: str = "",
) -> str:
    raw = f"{blob_hash}|{analyzer_id}|{__version__}|{config_fingerprint}|{extra}"
    return hashlib.sha256(raw.encode()).hexdigest()


class CacheStore:
    def __init__(self, cache_dir: Path, enabled: bool = True) -> None:
        self.enabled = enabled
        self.cache_dir = cache_dir
        self.db_path = cache_dir / "cache.sqlite"
        if enabled:
            cache_dir.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS kv (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at REAL DEFAULT (strftime('%s','now'))
                )
                """
            )
            self._conn.commit()
            self.hits = 0
            self.misses = 0
        else:
            self._conn = None
            self.hits = 0
            self.misses = 0

    def get(self, key: str) -> Any | None:
        if not self.enabled or self._conn is None:
            self.misses += 1
            return None
        row = self._conn.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
        if row is None:
            self.misses += 1
            return None
        self.hits += 1
        return json.loads(row[0])

    def set(self, key: str, value: Any) -> None:
        if not self.enabled or self._conn is None:
            return
        self._conn.execute(
            "INSERT OR REPLACE INTO kv(key, value) VALUES (?, ?)",
            (key, json.dumps(value)),
        )
        self._conn.commit()

    def stats(self) -> dict[str, int]:
        return {"hits": self.hits, "misses": self.misses}

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
