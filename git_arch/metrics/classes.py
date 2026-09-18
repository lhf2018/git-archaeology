from __future__ import annotations

import lizard


def class_breakdown(source: str, path: str) -> list[dict]:
    """Group lizard methods into classes. Free functions are ignored."""
    try:
        result = lizard.analyze_file.analyze_source_code(path, source)
    except Exception:
        return []
    buckets: dict[str, dict] = {}
    for func in result.function_list:
        raw = func.name or ""
        if "::" not in raw:
            continue
        cls = raw.rsplit("::", 1)[0].split(".")[-1].strip()
        if not cls or cls.startswith("("):
            continue
        rec = buckets.setdefault(cls, {"name": cls, "complexity": 0, "methods": 0})
        rec["complexity"] += int(func.cyclomatic_complexity or 0)
        rec["methods"] += 1
    return sorted(buckets.values(), key=lambda c: c["name"])
