from __future__ import annotations

from pathlib import Path

from git_arch.cache.store import CacheStore
from git_arch.config.schema import AppConfig
from git_arch.metrics.aggregate import aggregate_modules
from git_arch.metrics.churn_complexity import ChurnComplexityMetric
from git_arch.metrics.complexity import ComplexityMetric
from git_arch.metrics.ownership import OwnershipMetric
from git_arch.models import HistoryGraph, TimeSeries


def compute_all_metrics(
    repo: Path,
    graph: HistoryGraph,
    cfg: AppConfig,
    cache: CacheStore,
) -> list[TimeSeries]:
    enabled = {name for name, mc in cfg.metrics.items() if mc.enabled}
    all_series: list[TimeSeries] = []

    complexity_series: list[TimeSeries] = []
    if "complexity" in enabled or "churn_complexity" in enabled:
        complexity_series = ComplexityMetric().compute(repo, graph, cfg, cache)
        if "complexity" in enabled:
            all_series.extend(complexity_series)

    if "churn_complexity" in enabled:
        all_series.extend(
            ChurnComplexityMetric().compute(
                repo, graph, cfg, cache, complexity_series=complexity_series
            )
        )

    if "ownership_fragmentation" in enabled:
        all_series.extend(OwnershipMetric().compute(repo, graph, cfg, cache))

    all_series.extend(aggregate_modules(all_series, depth=cfg.module_depth))
    return all_series
