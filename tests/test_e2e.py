from __future__ import annotations

from pathlib import Path

from git_arch.config.loader import parse_formats
from git_arch.config.schema import AppConfig
from git_arch.pipeline.analyze import run_analyze


def test_parse_formats_both_json():
    assert parse_formats("both") == ["md", "html"]
    assert parse_formats("both,json") == ["md", "html", "json"]
    assert parse_formats("md,html,json") == ["md", "html", "json"]


def test_end_to_end_fixture():
    fixture = Path(__file__).resolve().parents[1] / ".fixtures" / "decay-demo"
    if not (fixture / ".git").exists():
        return  # skip if fixture not prepared
    cfg = AppConfig()
    cfg.report.formats = ["md", "html", "json"]
    cfg.report.output = "archaeology-report-test"
    cfg.detection.sensitivity = "high"
    report, written = run_analyze(path="src", cfg=cfg, cwd=fixture)
    assert report.meta["file_count"] >= 1
    assert report.meta["commit_count"] >= 5
    assert any(p.suffix == ".md" for p in written)
    assert any(p.suffix == ".html" for p in written)
    assert report.hotspots
