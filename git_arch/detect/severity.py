from __future__ import annotations

from git_arch.config.schema import Sensitivity
from git_arch.models import Severity


PENALTY: dict[Sensitivity, float] = {
    "low": 8.0,
    "medium": 4.0,
    "high": 2.0,
}

WEIGHT_DEFAULTS = {
    "complexity": 1.0,
    "churn_complexity": 1.2,
    "ownership_fragmentation": 0.8,
}


def score_to_severity(score: float) -> Severity:
    if score >= 2.0:
        return "high"
    if score >= 0.8:
        return "medium"
    return "low"


def severity_rank(s: Severity) -> int:
    return {"low": 1, "medium": 2, "high": 3}[s]


def max_severity(a: Severity, b: Severity) -> Severity:
    return a if severity_rank(a) >= severity_rank(b) else b
