from __future__ import annotations

from collections import defaultdict
from pathlib import PurePosixPath

from git_arch.git.parse import short_sha, summarize_message
from git_arch.models import ArchaeologyReport, ChangePoint, DecayEvent

SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".java"}

KIND_LABEL = {
    "complexity": "复杂度",
    "churn_complexity": "改动热度",
    "ownership_fragmentation": "所有权",
}

TAG_LABEL = {
    "giant_commit": "巨型提交",
    "ownership_burst": "所有权分散",
    "hotfix_cluster": "修复密集",
    "churn_spike": "高频改动",
    "coupling_hint": "跨模块耦合",
}

LANG_LABEL = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
}

SEV_RANK = {"low": 1, "medium": 2, "high": 3}


def area_of(path: str) -> str:
    parts = path.replace("\\", "/").split("/")
    return parts[0] if parts and parts[0] else "(root)"


def is_source_file(path: str) -> bool:
    return PurePosixPath(path.replace("\\", "/")).suffix.lower() in SOURCE_SUFFIXES


def language_of(path: str) -> str:
    suffix = PurePosixPath(path.replace("\\", "/")).suffix.lower()
    return LANG_LABEL.get(suffix, suffix.lstrip(".") or "—")


def kind_of(metric: str) -> str:
    return KIND_LABEL.get(metric, metric)


def tag_of(hypothesis_id: str | None) -> str:
    return TAG_LABEL.get(hypothesis_id or "", "指标突变")


def action_of(tag: str, kind: str) -> str:
    if tag == "修复密集":
        return "补测试"
    if tag in {"所有权分散"} or kind == "所有权":
        return "定主责"
    if tag == "跨模块耦合":
        return "解耦"
    if kind == "改动热度":
        return "隔离"
    return "拆分"


def _fmt(v: float) -> str:
    if abs(v) >= 100:
        return f"{v:.0f}"
    if abs(v) >= 10:
        return f"{v:.1f}"
    return f"{v:.2f}"


def _pct(before: float, after: float) -> str:
    if abs(before) < 1e-9:
        return "—"
    pct = (after - before) / abs(before) * 100
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.0f}%"


def _meter(before: float, after: float) -> dict[str, int | bool]:
    peak = max(abs(before), abs(after), 1e-9)
    return {
        "before_pct": int(round(abs(before) / peak * 100)),
        "after_pct": int(round(abs(after) / peak * 100)),
        "up": after >= before,
    }


def build_view(report: ArchaeologyReport) -> dict:
    """Group file-level changes by top-level code area."""
    rows: list[dict] = []
    for event in report.events:
        for cp in event.change_points:
            if not is_source_file(cp.entity_id):
                continue
            rows.append(_row(event, cp))

    by_area: dict[str, list[dict]] = {}
    for row in rows:
        by_area.setdefault(row["area"], []).append(row)

    areas: list[dict] = []
    for name, changes in by_area.items():
        changes.sort(key=lambda r: (r["date"], r["path"], r["kind"]))
        files = sorted({c["path"] for c in changes})
        sev = max(changes, key=lambda c: SEV_RANK.get(c["severity"], 0))["severity"]
        kinds = []
        for c in changes:
            if c["kind"] not in kinds:
                kinds.append(c["kind"])
        chart = _chart_for_area(report, name, files)
        areas.append(
            {
                "name": name,
                "severity": sev,
                "kinds": kinds,
                "file_count": len(files),
                "change_count": len(changes),
                "top_file": _top_file(changes),
                "primary_kind": _primary_kind(changes),
                "spark": _ascii_spark(chart["values"]) if chart else "",
                "chart": chart,
                "changes": changes,
            }
        )

    areas.sort(
        key=lambda a: (
            -SEV_RANK.get(a["severity"], 0),
            -a["change_count"],
            a["name"],
        )
    )
    return {"areas": areas, "lanes": rows}


def _row(event: DecayEvent, cp: ChangePoint) -> dict:
    tag = tag_of(event.hypothesis_id)
    kind = kind_of(cp.metric)
    meter = _meter(cp.before_value, cp.after_value)
    return {
        "date": event.timestamp.strftime("%Y-%m-%d"),
        "sha": short_sha(event.commit_sha),
        "author": event.author_name or "—",
        "message": summarize_message(event.commit_message, 56),
        "path": cp.entity_id,
        "file": PurePosixPath(cp.entity_id).name,
        "area": area_of(cp.entity_id),
        "lang": language_of(cp.entity_id),
        "kind": kind,
        "tag": tag,
        "action": action_of(tag, kind),
        "before": _fmt(cp.before_value),
        "after": _fmt(cp.after_value),
        "before_raw": round(cp.before_value, 2),
        "after_raw": round(cp.after_value, 2),
        "pct": _pct(cp.before_value, cp.after_value),
        "severity": cp.severity,
        "before_pct": meter["before_pct"],
        "after_pct": meter["after_pct"],
        "up": meter["up"],
    }


def _primary_kind(changes: list[dict]) -> str:
    counts: dict[str, int] = {}
    for c in changes:
        counts[c["kind"]] = counts.get(c["kind"], 0) + 1
    return max(counts, key=lambda k: counts[k]) if counts else "—"


def _top_file(changes: list[dict]) -> str:
    best = ""
    best_score = -1.0
    for c in changes:
        score = abs(c["after_raw"] - c["before_raw"]) + SEV_RANK.get(c["severity"], 0) * 10
        if score > best_score:
            best_score = score
            best = c["path"]
    return best


def _chart_for_area(report: ArchaeologyReport, area: str, files: list[str]) -> dict | None:
    wanted = set(files)
    best = None
    best_v = -1.0
    for series in report.global_series:
        if series.entity_kind != "file" or series.metric != "complexity":
            continue
        if area_of(series.entity_id) != area:
            continue
        if wanted and series.entity_id not in wanted:
            continue
        if not series.points:
            continue
        value = series.points[-1].value
        if value > best_v:
            best_v = value
            best = series
    if best is None:
        return None
    points = best.points
    if len(points) > 36:
        step = len(points) / 36
        points = [points[int(i * step)] for i in range(36)]
    return {
        "file": best.entity_id,
        "labels": [p.timestamp.strftime("%m-%d") for p in points],
        "values": [round(p.value, 2) for p in points],
    }


def _ascii_spark(vals: list[float], width: int = 32) -> str:
    if not vals:
        return ""
    if len(vals) > width:
        step = len(vals) / width
        vals = [vals[int(i * step)] for i in range(width)]
    lo, hi = min(vals), max(vals)
    blocks = "▁▂▃▄▅▆▇█"
    if hi - lo < 1e-12:
        return blocks[3] * len(vals)
    return "".join(blocks[int((v - lo) / (hi - lo) * (len(blocks) - 1))] for v in vals)


def build_class_view(report: ArchaeologyReport, *, multi_limit: int = 20, single_limit: int = 24) -> dict:
    """Split class series into co-evolving commits and per-class timelines."""
    jumps_by_commit: dict[str, list[dict]] = defaultdict(list)
    singles: list[dict] = []

    for series in report.global_series:
        if series.entity_kind != "class" or series.metric != "class_complexity":
            continue
        if "#" not in series.entity_id or len(series.points) < 2:
            continue
        path, name = series.entity_id.rsplit("#", 1)
        pts = series.points
        jumps: list[dict] = []
        for i in range(1, len(pts)):
            before, after = pts[i - 1].value, pts[i].value
            if abs(after - before) < 1:
                continue
            meter = _meter(before, after)
            jump = {
                "date": pts[i].timestamp.strftime("%Y-%m-%d"),
                "sha": short_sha(pts[i].commit_sha),
                "commit_sha": pts[i].commit_sha,
                "author": (pts[i].extras or {}).get("author") or "—",
                "message": summarize_message((pts[i].extras or {}).get("message") or "", 56),
                "name": name,
                "path": path,
                "file": PurePosixPath(path).name,
                "area": area_of(path),
                "lang": language_of(path),
                "methods": (pts[i].extras or {}).get("methods") or 0,
                "before": _fmt(before),
                "after": _fmt(after),
                "before_raw": before,
                "after_raw": after,
                "pct": _pct(before, after),
                "before_pct": meter["before_pct"],
                "after_pct": meter["after_pct"],
                "up": meter["up"],
            }
            jumps.append(jump)
            jumps_by_commit[pts[i].commit_sha].append(jump)
        if not jumps:
            continue
        chart_pts = pts
        if len(chart_pts) > 36:
            step = len(chart_pts) / 36
            chart_pts = [chart_pts[int(i * step)] for i in range(36)]
        values = [round(p.value, 2) for p in chart_pts]
        biggest = max(jumps, key=lambda j: abs(j["after_raw"] - j["before_raw"]))
        singles.append(
            {
                "name": name,
                "path": path,
                "file": PurePosixPath(path).name,
                "area": area_of(path),
                "lang": language_of(path),
                "start": _fmt(pts[0].value),
                "end": _fmt(pts[-1].value),
                "delta": round(pts[-1].value - pts[0].value, 1),
                "methods": (pts[-1].extras or {}).get("methods") or 0,
                "spark": _ascii_spark(values),
                "chart": {
                    "labels": [p.timestamp.strftime("%m-%d") for p in chart_pts],
                    "values": values,
                },
                "jumps": jumps[:6],
                "author": biggest["author"],
                "jump_date": biggest["date"],
                "jump_sha": biggest["sha"],
            }
        )

    singles.sort(key=lambda s: abs(s["delta"]), reverse=True)

    multi: list[dict] = []
    for sha, jumps in jumps_by_commit.items():
        uniq: dict[str, dict] = {}
        for jump in jumps:
            uniq[f"{jump['path']}#{jump['name']}"] = jump
        if len(uniq) < 2:
            continue
        classes = sorted(uniq.values(), key=lambda j: abs(j["after_raw"] - j["before_raw"]), reverse=True)
        head = classes[0]
        areas = []
        for c in classes:
            if c["area"] not in areas:
                areas.append(c["area"])
        multi.append(
            {
                "date": head["date"],
                "sha": head["sha"],
                "author": head["author"],
                "message": head["message"],
                "areas": areas,
                "class_count": len(classes),
                "classes": classes[:12],
            }
        )
    multi.sort(key=lambda m: (-m["class_count"], m["date"]))

    return {
        "multi_total": len(multi),
        "single_total": len(singles),
        "multi": multi[:multi_limit],
        "single": singles[:single_limit],
    }
