from __future__ import annotations

import re

FIX_RE = re.compile(
    r"\b(fix|fixes|fixed|hotfix|revert|bugfix|patch)\b",
    re.IGNORECASE,
)


def is_fix_commit(message: str) -> bool:
    return bool(FIX_RE.search(message or ""))


def short_sha(sha: str, n: int = 7) -> str:
    return sha[:n] if sha else ""


def summarize_message(message: str, limit: int = 72) -> str:
    msg = (message or "").strip().splitlines()[0] if message else ""
    if len(msg) <= limit:
        return msg
    return msg[: limit - 1] + "…"
