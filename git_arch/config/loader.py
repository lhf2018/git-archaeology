from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from git_arch.config.schema import (
    AppConfig,
    AttributionConfig,
    CacheConfig,
    DetectionConfig,
    MetricConfig,
    ReportConfig,
)


def _metric_from_dict(data: dict[str, Any] | None) -> MetricConfig:
    data = data or {}
    return MetricConfig(
        enabled=bool(data.get("enabled", True)),
        weight=float(data.get("weight", 1.0)),
        aggregate=str(data.get("aggregate", "sum")),
        churn_window=data.get("churn_window"),
    )


def load_config(repo_root: Path, cli_overrides: dict[str, Any] | None = None) -> AppConfig:
    cfg = AppConfig()
    yml_path = repo_root / ".git-arch.yml"
    if yml_path.is_file():
        with yml_path.open(encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        cfg = _merge_yaml(cfg, raw)

    overrides = cli_overrides or {}
    if sens := overrides.get("sensitivity"):
        cfg.detection.sensitivity = sens  # type: ignore[assignment]
    if metrics := overrides.get("metrics"):
        wanted = {m.strip() for m in metrics.split(",") if m.strip()}
        for name, mc in cfg.metrics.items():
            mc.enabled = name in wanted
    if show_authors := overrides.get("show_authors"):
        cfg.attribution.show_authors = bool(show_authors)
    if formats := overrides.get("formats"):
        cfg.report.formats = formats
    if output := overrides.get("output"):
        cfg.report.output = output
    if no_cache := overrides.get("no_cache"):
        cfg.cache.enabled = not bool(no_cache)
    return cfg


def _merge_yaml(cfg: AppConfig, raw: dict[str, Any]) -> AppConfig:
    if "metrics" in raw and isinstance(raw["metrics"], dict):
        for name, data in raw["metrics"].items():
            cfg.metrics[name] = _metric_from_dict(data)
    if "detection" in raw and isinstance(raw["detection"], dict):
        d = raw["detection"]
        cfg.detection = DetectionConfig(
            algorithm=str(d.get("algorithm", cfg.detection.algorithm)),
            sensitivity=str(d.get("sensitivity", cfg.detection.sensitivity)),  # type: ignore[arg-type]
            min_size=int(d.get("min_size", cfg.detection.min_size)),
            short_seq_threshold=int(
                d.get("short_seq_threshold", cfg.detection.short_seq_threshold)
            ),
        )
    if "attribution" in raw and isinstance(raw["attribution"], dict):
        a = raw["attribution"]
        cfg.attribution = AttributionConfig(
            show_authors=bool(a.get("show_authors", cfg.attribution.show_authors)),
            giant_commit_lines=int(
                a.get("giant_commit_lines", cfg.attribution.giant_commit_lines)
            ),
            ownership_author_delta=int(
                a.get("ownership_author_delta", cfg.attribution.ownership_author_delta)
            ),
            hotfix_ratio=float(a.get("hotfix_ratio", cfg.attribution.hotfix_ratio)),
            hotfix_window=int(a.get("hotfix_window", cfg.attribution.hotfix_window)),
        )
    if "report" in raw and isinstance(raw["report"], dict):
        r = raw["report"]
        cfg.report = ReportConfig(
            formats=list(r.get("formats", cfg.report.formats)),
            output=str(r.get("output", cfg.report.output)),
            top_hotspots=int(r.get("top_hotspots", cfg.report.top_hotspots)),
            top_events=int(r.get("top_events", cfg.report.top_events)),
        )
    if "ignore" in raw and isinstance(raw["ignore"], list):
        cfg.ignore = [str(x) for x in raw["ignore"]]
    if "cache" in raw and isinstance(raw["cache"], dict):
        c = raw["cache"]
        cfg.cache = CacheConfig(
            dir=str(c.get("dir", cfg.cache.dir)),
            enabled=bool(c.get("enabled", cfg.cache.enabled)),
        )
    if "module_depth" in raw:
        cfg.module_depth = int(raw["module_depth"])
    if "blame_stride" in raw:
        cfg.blame_stride = int(raw["blame_stride"])
    return cfg


def parse_formats(format_arg: str | None) -> list[str]:
    if not format_arg:
        return ["md", "html"]
    raw = format_arg.strip().lower()
    if raw in {"both", "md,html", "html,md"}:
        return ["md", "html"]
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    out: list[str] = []
    allowed = {"md", "html", "json", "sarif"}
    for p in parts:
        if p == "both":
            for f in ("md", "html"):
                if f not in out:
                    out.append(f)
        elif p in allowed and p not in out:
            out.append(p)
    return out or ["md", "html"]
