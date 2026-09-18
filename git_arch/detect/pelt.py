from __future__ import annotations

import numpy as np

from git_arch.config.schema import AppConfig
from git_arch.detect.normalize import zscore
from git_arch.detect.severity import PENALTY, WEIGHT_DEFAULTS, score_to_severity
from git_arch.detect.threshold import threshold_detect
from git_arch.models import ChangePoint, TimeSeries


def detect_changepoints(series: TimeSeries, cfg: AppConfig) -> list[ChangePoint]:
    points = series.points
    if len(points) < 4:
        return []

    values = [p.value for p in points]
    # skip constant
    if max(values) - min(values) < 1e-12:
        return []

    signal = zscore(values)
    weight = WEIGHT_DEFAULTS.get(series.metric, 1.0)
    if series.metric in cfg.metrics:
        weight = cfg.metrics[series.metric].weight

    if len(points) < cfg.detection.short_seq_threshold:
        indices = threshold_detect(signal)
    else:
        indices = _pelt_detect(signal, cfg)

    results: list[ChangePoint] = []
    for idx in indices:
        if idx <= 0 or idx >= len(points):
            continue
        left = values[max(0, idx - 3) : idx]
        right = values[idx : min(len(values), idx + 3)]
        before = float(np.mean(left)) if left else values[idx - 1]
        after = float(np.mean(right)) if right else values[idx]
        delta = after - before
        # effect size vs global std
        std = float(np.std(values)) or 1.0
        confidence = float(min(1.0, abs(delta) / (2 * std)))
        score = abs(delta / std) * weight * max(confidence, 0.1)
        results.append(
            ChangePoint(
                entity_id=series.entity_id,
                metric=series.metric,
                commit_sha=points[idx].commit_sha,
                timestamp=points[idx].timestamp,
                before_value=before,
                after_value=after,
                delta=delta,
                confidence=confidence,
                severity=score_to_severity(score),
            )
        )
    return results


def _pelt_detect(signal: np.ndarray, cfg: AppConfig) -> list[int]:
    try:
        import ruptures as rpt
    except ImportError:
        return threshold_detect(signal)

    pen = PENALTY.get(cfg.detection.sensitivity, 4.0)  # type: ignore[arg-type]
    algo = rpt.Pelt(model="rbf", min_size=cfg.detection.min_size).fit(signal.reshape(-1, 1))
    # predict returns end indices of segments; last is len
    bkps = algo.predict(pen=pen)
    return [b for b in bkps[:-1] if 0 < b < len(signal)]
