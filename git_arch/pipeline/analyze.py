from __future__ import annotations

import json
import time
from pathlib import Path

from git_arch import __version__
from git_arch.attribute.rules import attribute_events
from git_arch.attribute.templates import render_causal_chain
from git_arch.cache.store import CacheStore
from git_arch.config.schema import AppConfig
from git_arch.detect import run_detection
from git_arch.git.history import build_history_graph
from git_arch.git.repo import find_repo_root, resolve_branch
from git_arch.metrics.registry import compute_all_metrics
from git_arch.models import ArchaeologyReport, DecayEvent, HotspotProfile, TimeSeries
from git_arch.report.html import write_html
from git_arch.report.json_export import write_json
from git_arch.report.markdown import write_markdown
from git_arch.report.suggestions import (
    global_actions,
    suggestions_for_event,
    suggestions_for_hotspot,
)


LAST_RUN = ".git-arch/last_run.json"


def run_analyze(
    *,
    path: str | None = None,
    since: str | None = None,
    until: str | None = None,
    branch: str | None = None,
    max_commits: int | None = None,
    incremental: bool = False,
    cfg: AppConfig,
    cwd: Path | None = None,
) -> tuple[ArchaeologyReport, list[Path]]:
    t0 = time.perf_counter()
    repo = find_repo_root(cwd)
    br = resolve_branch(repo, branch)

    if incremental:
        since = _since_from_last_run(repo) or since

    cache_dir = repo / cfg.cache.dir
    cache = CacheStore(cache_dir, enabled=cfg.cache.enabled)

    graph = build_history_graph(
        repo,
        branch=br,
        path_filter=path,
        since=since,
        until=until,
        max_commits=max_commits,
        ignore=cfg.ignore,
    )

    series = compute_all_metrics(repo, graph, cfg, cache)
    _cps, events = run_detection(series, cfg)
    events = attribute_events(events, graph, cfg)

    for event in events:
        hint = suggestions_for_event(event)
        event.causal_chain = render_causal_chain(event, hint)

    hotspots = _build_hotspots(series, events, cfg.report.top_hotspots)
    actions = global_actions(hotspots, events)

    ranked_events = sorted(events, key=lambda e: (e.timestamp, e.commit_sha))

    elapsed = round(time.perf_counter() - t0, 2)
    stats = cache.stats()
    report = ArchaeologyReport(
        meta={
            "repo": str(repo),
            "branch": br,
            "path": path,
            "commit_count": len(graph.commits),
            "file_count": len(graph.files),
            "event_count": len(events),
            "elapsed_sec": elapsed,
            "version": __version__,
        },
        summary={},
        global_series=series,
        events=ranked_events if ranked_events else events,
        hotspots=hotspots,
        actions=actions,
        appendix={
            "algorithm": cfg.detection.algorithm,
            "sensitivity": cfg.detection.sensitivity,
            "cache_hits": stats["hits"],
            "cache_misses": stats["misses"],
            "truncated": graph.truncated,
            "authors_anonymized": not cfg.attribution.show_authors,
        },
    )

    # Fill summary for consumers
    report.summary = {
        "top_hotspots": [h.path for h in hotspots[:5]],
        "top_events": [e.commit_sha for e in report.events[:3]],
    }

    written = _write_reports(report, repo, cfg)
    _save_last_run(repo, graph.commits[-1].sha if graph.commits else None)
    cache.close()
    return report, written


def _build_hotspots(
    series: list[TimeSeries],
    events: list[DecayEvent],
    top_n: int,
) -> list[HotspotProfile]:
    file_series = [s for s in series if s.entity_kind == "file"]
    by_path: dict[str, dict[str, TimeSeries]] = {}
    for s in file_series:
        by_path.setdefault(s.entity_id, {})[s.metric] = s

    events_by_path: dict[str, list[DecayEvent]] = {}
    for e in events:
        for p in e.entity_ids:
            if p in by_path:
                events_by_path.setdefault(p, []).append(e)

    scored: list[tuple[float, HotspotProfile]] = []
    for path, metrics in by_path.items():
        current = {
            name: (ts.points[-1].value if ts.points else 0.0) for name, ts in metrics.items()
        }
        score = (
            current.get("complexity", 0) * 1.0
            + current.get("churn_complexity", 0) * 0.01
            + current.get("ownership_fragmentation", 0) * 20
            + len(events_by_path.get(path, [])) * 5
        )
        profile = HotspotProfile(
            path=path,
            current_metrics=current,
            series=list(metrics.values()),
            events=events_by_path.get(path, []),
            suggestions=[],
        )
        profile.suggestions = suggestions_for_hotspot(profile)
        scored.append((score, profile))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:top_n]]


def _write_reports(report: ArchaeologyReport, repo: Path, cfg: AppConfig) -> list[Path]:
    out = cfg.report.output
    base = Path(out)
    if not base.is_absolute():
        base = repo / base

    formats = cfg.report.formats
    written: list[Path] = []

    # If output has a known suffix and single format, use as file path
    suffix = base.suffix.lower().lstrip(".")
    if suffix in {"md", "html", "json"} and len(formats) == 1:
        targets = {formats[0]: base}
    else:
        # treat as basename
        stem = base
        if suffix in {"md", "html", "json"}:
            stem = base.with_suffix("")
        targets = {fmt: Path(f"{stem}.{fmt if fmt != 'md' else 'md'}") for fmt in formats}
        # normalize md
        targets = {fmt: Path(str(stem) + (".md" if fmt == "md" else f".{fmt}")) for fmt in formats}

    for fmt, path in targets.items():
        if fmt == "md":
            written.append(write_markdown(report, path))
        elif fmt == "html":
            written.append(write_html(report, path))
        elif fmt == "json":
            written.append(write_json(report, path))
        elif fmt == "sarif":
            # M2 stub: write empty-ish json note
            path.write_text(
                json.dumps({"version": "2.1.0", "runs": [], "note": "SARIF reserved for M2"}),
                encoding="utf-8",
            )
            written.append(path)
    return written


def _save_last_run(repo: Path, sha: str | None) -> None:
    path = repo / LAST_RUN
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"last_commit": sha}, indent=2), encoding="utf-8")


def _since_from_last_run(repo: Path) -> str | None:
    path = repo / LAST_RUN
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    sha = data.get("last_commit")
    if not sha:
        return None
    # analyze commits after last_commit — approximate with --since not ideal;
    # store marker and use git rev-list; for MVP return None and rely on cache.
    # Better: pass as since_commit via environment — we encode as "commit+1" using
    # git log -1 --format=%cI of that commit as since (inclusive overlap OK with cache).
    from git_arch.git.repo import run_git

    iso = run_git(["show", "-s", "--format=%cI", sha], repo, check=False).strip()
    return iso or None
