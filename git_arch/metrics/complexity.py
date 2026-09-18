from __future__ import annotations

from pathlib import Path

import lizard

from git_arch.cache.store import CacheStore, make_cache_key
from git_arch.config.schema import AppConfig
from git_arch.git.history import show_blob
from git_arch.metrics.classes import class_breakdown
from git_arch.models import HistoryGraph, MetricPoint, TimeSeries


class ComplexityMetric:
    name = "complexity"

    def compute(
        self,
        repo: Path,
        graph: HistoryGraph,
        cfg: AppConfig,
        cache: CacheStore,
    ) -> list[TimeSeries]:
        mc = cfg.metrics.get(self.name)
        aggregate = (mc.aggregate if mc else "sum") or "sum"
        fingerprint = cfg.config_fingerprint()
        commit_index = {c.sha: c for c in graph.commits}
        series_list: list[TimeSeries] = []

        for path, revs in graph.files.items():
            points: list[MetricPoint] = []
            class_points: dict[str, list[MetricPoint]] = {}
            for rev in revs:
                commit = commit_index.get(rev.commit_sha)
                if not commit:
                    continue
                value, classes = self._inspect_blob(
                    repo, rev.blob_hash, path, aggregate, fingerprint, cache
                )
                points.append(
                    MetricPoint(
                        commit_sha=rev.commit_sha,
                        timestamp=commit.timestamp,
                        value=float(value),
                        extras={"blob": rev.blob_hash},
                    )
                )
                for item in classes:
                    key = f"{path}#{item['name']}"
                    class_points.setdefault(key, []).append(
                        MetricPoint(
                            commit_sha=rev.commit_sha,
                            timestamp=commit.timestamp,
                            value=float(item["complexity"]),
                            extras={
                                "author": commit.author_name,
                                "message": commit.message,
                                "methods": item["methods"],
                                "class": item["name"],
                                "path": path,
                            },
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
            for key, cpoints in class_points.items():
                series_list.append(
                    TimeSeries(
                        entity_id=key,
                        entity_kind="class",
                        metric="class_complexity",
                        points=cpoints,
                    )
                )
        return series_list

    def _inspect_blob(
        self,
        repo: Path,
        blob_hash: str,
        path: str,
        aggregate: str,
        fingerprint: str,
        cache: CacheStore,
    ) -> tuple[float, list[dict]]:
        key = make_cache_key(blob_hash, "complexity", fingerprint, aggregate + ":cls1")
        cached = cache.get(key)
        if cached is not None and "classes" in cached:
            return float(cached["value"]), list(cached["classes"])

        source = show_blob(repo, blob_hash)
        value = analyze_complexity(source, path, aggregate)
        classes = class_breakdown(source, path)
        cache.set(key, {"value": value, "classes": classes})
        return value, classes


def analyze_complexity(source: str, path: str, aggregate: str = "sum") -> float:
    try:
        # lizard expects a filename for language detection
        result = lizard.analyze_file.analyze_source_code(path, source)
    except Exception:
        return 0.0
    ccn_values = [f.cyclomatic_complexity for f in result.function_list]
    if not ccn_values:
        # file-level fallback: rough heuristic
        return float(max(1, source.count("\n") // 50))
    if aggregate == "max":
        return float(max(ccn_values))
    return float(sum(ccn_values))
