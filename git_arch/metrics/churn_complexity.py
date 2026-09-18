from __future__ import annotations

from pathlib import Path

from git_arch.cache.store import CacheStore
from git_arch.config.schema import AppConfig
from git_arch.models import HistoryGraph, MetricPoint, TimeSeries


class ChurnComplexityMetric:
    name = "churn_complexity"

    def compute(
        self,
        repo: Path,
        graph: HistoryGraph,
        cfg: AppConfig,
        cache: CacheStore,
        complexity_series: list[TimeSeries] | None = None,
    ) -> list[TimeSeries]:
        mc = cfg.metrics.get(self.name)
        window = mc.churn_window if mc else None
        commit_index = {c.sha: c for c in graph.commits}

        cx_map: dict[str, dict[str, float]] = {}
        for ts in complexity_series or []:
            cx_map[ts.entity_id] = {p.commit_sha: p.value for p in ts.points}

        series_list: list[TimeSeries] = []
        for path, revs in graph.files.items():
            points: list[MetricPoint] = []
            for i, rev in enumerate(revs):
                commit = commit_index.get(rev.commit_sha)
                if not commit:
                    continue
                if window:
                    churn = min(i + 1, window)
                else:
                    churn = i + 1
                cx = cx_map.get(path, {}).get(rev.commit_sha, 0.0)
                points.append(
                    MetricPoint(
                        commit_sha=rev.commit_sha,
                        timestamp=commit.timestamp,
                        value=float(churn) * float(cx),
                        extras={"churn": churn, "complexity": cx},
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
