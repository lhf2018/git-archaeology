from __future__ import annotations

from pathlib import PurePosixPath

from git_arch.models import MetricPoint, TimeSeries


def aggregate_modules(series_list: list[TimeSeries], depth: int = 2) -> list[TimeSeries]:
    """Aggregate file-level series into directory modules."""
    buckets: dict[tuple[str, str], dict[str, list[MetricPoint]]] = {}
    # key: (module, metric) -> commit_sha -> list of values at that commit
    for ts in series_list:
        if ts.entity_kind != "file":
            continue
        module = module_of(ts.entity_id, depth)
        key = (module, ts.metric)
        by_commit = buckets.setdefault(key, {})
        for p in ts.points:
            by_commit.setdefault(p.commit_sha, []).append(p)

    out: list[TimeSeries] = []
    for (module, metric), by_commit in buckets.items():
        points: list[MetricPoint] = []
        for sha, pts in by_commit.items():
            avg = sum(p.value for p in pts) / len(pts)
            points.append(
                MetricPoint(
                    commit_sha=sha,
                    timestamp=pts[0].timestamp,
                    value=avg,
                    extras={"n_files": len(pts)},
                )
            )
        points.sort(key=lambda p: (p.timestamp, p.commit_sha))
        out.append(
            TimeSeries(entity_id=module, entity_kind="module", metric=metric, points=points)
        )
    return out


def module_of(path: str, depth: int) -> str:
    parts = PurePosixPath(path.replace("\\", "/")).parts
    if len(parts) <= 1:
        return parts[0] if parts else "."
    return "/".join(parts[: min(depth, len(parts) - 1)]) or "."
