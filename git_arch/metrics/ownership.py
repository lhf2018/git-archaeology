from __future__ import annotations

from pathlib import Path

from git_arch.cache.store import CacheStore, make_cache_key
from git_arch.config.schema import AppConfig
from git_arch.git.blame import blame_author_counts
from git_arch.metrics.base import entropy_normalized, gini
from git_arch.models import HistoryGraph, MetricPoint, TimeSeries


class OwnershipMetric:
    name = "ownership_fragmentation"

    def compute(
        self,
        repo: Path,
        graph: HistoryGraph,
        cfg: AppConfig,
        cache: CacheStore,
    ) -> list[TimeSeries]:
        fingerprint = cfg.config_fingerprint()
        stride = max(1, cfg.blame_stride)
        commit_index = {c.sha: c for c in graph.commits}
        series_list: list[TimeSeries] = []

        for path, revs in graph.files.items():
            points: list[MetricPoint] = []
            last_value = 0.0
            last_extras: dict = {"authors": 0, "gini": 0.0}
            for i, rev in enumerate(revs):
                commit = commit_index.get(rev.commit_sha)
                if not commit:
                    continue
                # Always compute first/last; stride intermediate
                should = i == 0 or i == len(revs) - 1 or (i % stride == 0)
                if should:
                    key = make_cache_key(
                        rev.blob_hash, "ownership", fingerprint, rev.commit_sha
                    )
                    cached = cache.get(key)
                    if cached is not None:
                        value = float(cached["value"])
                        extras = cached.get("extras", {})
                    else:
                        counts = blame_author_counts(repo, rev.commit_sha, path)
                        value, n_authors = entropy_normalized(counts)
                        extras = {
                            "authors": n_authors,
                            "gini": gini(counts),
                            "author_keys": list(counts.keys()),
                        }
                        cache.set(key, {"value": value, "extras": extras})
                    last_value = value
                    last_extras = extras
                points.append(
                    MetricPoint(
                        commit_sha=rev.commit_sha,
                        timestamp=commit.timestamp,
                        value=float(last_value),
                        extras=dict(last_extras),
                    )
                )
            if points:
                series_list.append(
                    TimeSeries(
                        entity_id=path,
                        entity_kind="file",
                        metric=self.name,
                        points=points,
                    )
                )
        return series_list
