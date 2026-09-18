from __future__ import annotations

import math
from pathlib import Path
from typing import Protocol

from git_arch.cache.store import CacheStore, make_cache_key
from git_arch.config.schema import AppConfig
from git_arch.git.blame import blame_author_counts
from git_arch.git.history import show_blob
from git_arch.models import HistoryGraph, MetricPoint, TimeSeries


class MetricCalculator(Protocol):
    name: str

    def compute(
        self,
        repo: Path,
        graph: HistoryGraph,
        cfg: AppConfig,
        cache: CacheStore,
    ) -> list[TimeSeries]:
        ...


def entropy_normalized(counts: dict[str, int]) -> tuple[float, int]:
    total = sum(counts.values())
    if total <= 0:
        return 0.0, 0
    n = len(counts)
    probs = [c / total for c in counts.values()]
    h = -sum(p * math.log2(p) for p in probs if p > 0)
    denom = math.log2(max(n, 2))
    return (h / denom if denom else 0.0), n


def gini(counts: dict[str, int]) -> float:
    xs = sorted(counts.values())
    if not xs:
        return 0.0
    n = len(xs)
    total = sum(xs)
    if total == 0:
        return 0.0
    cum = 0.0
    for i, x in enumerate(xs, start=1):
        cum += i * x
    return (2 * cum) / (n * total) - (n + 1) / n
