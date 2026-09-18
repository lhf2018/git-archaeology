from __future__ import annotations

from git_arch.git.parse import short_sha, summarize_message
from git_arch.models import DecayEvent


METRIC_LABELS = {
    "complexity": "复杂度",
    "churn_complexity": "churn×复杂度",
    "ownership_fragmentation": "所有权碎片化",
}


def render_causal_chain(event: DecayEvent, action_hint: str) -> str:
    cp = max(event.change_points, key=lambda c: abs(c.delta))
    date = event.timestamp.strftime("%Y-%m-%d")
    sha = short_sha(event.commit_sha)
    summary = summarize_message(event.commit_message) or "相关提交"
    path = cp.entity_id
    label = METRIC_LABELS.get(cp.metric, cp.metric)
    before = _fmt(cp.before_value)
    after = _fmt(cp.after_value)
    delta_pct = _delta_pct(cp.before_value, cp.after_value)
    hypo = event.hypothesis_label or "指标突变"
    return (
        f"{date} `{sha}`（{summary}）导致 `{path}` 的 {label} "
        f"从 {before} → {after}（Δ {delta_pct}）。"
        f"病因假设：{hypo}。建议：{action_hint}"
    )


def _fmt(v: float) -> str:
    if abs(v) >= 100:
        return f"{v:.0f}"
    if abs(v) >= 10:
        return f"{v:.1f}"
    return f"{v:.2f}"


def _delta_pct(before: float, after: float) -> str:
    if abs(before) < 1e-9:
        return "n/a"
    pct = (after - before) / abs(before) * 100
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.0f}%"
