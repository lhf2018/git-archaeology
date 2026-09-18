from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from git_arch.models import ArchaeologyReport


def _json_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(type(obj))


def write_json(report: ArchaeologyReport, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(report)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default),
        encoding="utf-8",
    )
    return path
