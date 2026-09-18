from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Literal


Sensitivity = Literal["low", "medium", "high"]


@dataclass
class MetricConfig:
    enabled: bool = True
    weight: float = 1.0
    aggregate: str = "sum"  # complexity: sum | max
    churn_window: int | None = None


@dataclass
class DetectionConfig:
    algorithm: str = "pelt"
    sensitivity: Sensitivity = "medium"
    min_size: int = 3
    short_seq_threshold: int = 20


@dataclass
class AttributionConfig:
    show_authors: bool = False
    giant_commit_lines: int = 500
    ownership_author_delta: int = 2
    hotfix_ratio: float = 0.4
    hotfix_window: int = 10


@dataclass
class ReportConfig:
    formats: list[str] = field(default_factory=lambda: ["md", "html"])
    output: str = "archaeology-report"
    top_hotspots: int = 10
    top_events: int = 20


@dataclass
class CacheConfig:
    dir: str = ".git-arch/cache"
    enabled: bool = True


@dataclass
class AppConfig:
    metrics: dict[str, MetricConfig] = field(
        default_factory=lambda: {
            "complexity": MetricConfig(enabled=True, weight=1.0),
            "churn_complexity": MetricConfig(enabled=True, weight=1.2),
            "ownership_fragmentation": MetricConfig(enabled=True, weight=0.8),
        }
    )
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    attribution: AttributionConfig = field(default_factory=AttributionConfig)
    report: ReportConfig = field(default_factory=ReportConfig)
    ignore: list[str] = field(
        default_factory=lambda: [
            "vendor/**",
            "**/*.min.js",
            "**/node_modules/**",
            "**/.git-arch/**",
        ]
    )
    cache: CacheConfig = field(default_factory=CacheConfig)
    module_depth: int = 2
    blame_stride: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def config_fingerprint(self) -> str:
        """Fingerprint of settings that invalidate metric cache."""
        import hashlib
        import json

        payload = {
            "metrics": {
                k: {"enabled": v.enabled, "aggregate": v.aggregate, "churn_window": v.churn_window}
                for k, v in self.metrics.items()
            },
            "blame_stride": self.blame_stride,
        }
        raw = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


DEFAULT_CONFIG_YAML = """\
metrics:
  complexity: { enabled: true, weight: 1.0, aggregate: sum }
  churn_complexity: { enabled: true, weight: 1.2, churn_window: null }
  ownership_fragmentation: { enabled: true, weight: 0.8 }
detection:
  algorithm: pelt
  sensitivity: medium
attribution:
  show_authors: false
  giant_commit_lines: 500
report:
  formats: [md, html]
  output: archaeology-report
ignore:
  - "vendor/**"
  - "**/*.min.js"
  - "**/node_modules/**"
cache:
  dir: .git-arch/cache
"""
