from __future__ import annotations

from git_arch.models import DecayEvent, HotspotProfile, TimeSeries


SUGGESTIONS_BY_RULE = {
    "giant_commit": "评估拆分该热点文件；为大块逻辑补边界测试后再改。",
    "ownership_burst": "明确 CODEOWNERS / 缩小评审范围，避免多头修改同一核心文件。",
    "hotfix_cluster": "优先补回归测试，短期冻结非必要功能改动。",
    "churn_spike": "将高频改动区与稳定区隔离，考虑提取稳定接口。",
    "coupling_hint": "梳理同提交共现模块，消除隐式耦合或合并职责边界。",
}


def suggestions_for_event(event: DecayEvent) -> str:
    return SUGGESTIONS_BY_RULE.get(
        event.hypothesis_id or "",
        "持续观察该文件指标，必要时在下一迭代安排重构。",
    )


def suggestions_for_hotspot(profile: HotspotProfile) -> list[str]:
    tips: list[str] = []
    cx = profile.current_metrics.get("complexity", 0)
    churn = profile.current_metrics.get("churn_complexity", 0)
    own = profile.current_metrics.get("ownership_fragmentation", 0)
    if cx >= 30 or churn >= 200:
        tips.append("复杂度/ churn 偏高：优先拆分模块并加单元测试。")
    if own >= 0.7:
        tips.append("所有权碎片化高：指定主维护者并限制并行大改。")
    if profile.events:
        tips.append(suggestions_for_event(profile.events[0]))
    if not tips:
        tips.append("当前指标可控：改动前阅读相关拐点因果链即可。")
    # dedupe
    seen: set[str] = set()
    out: list[str] = []
    for t in tips:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def global_actions(hotspots: list[HotspotProfile], events: list[DecayEvent]) -> list[str]:
    actions: list[str] = []
    high = [e for e in events if e.severity == "high"]
    if high:
        actions.append(f"优先处理 {len(high)} 个 high 严重度腐化事件（见拐点时间线）。")
    if hotspots:
        top = hotspots[0]
        actions.append(f"本周聚焦热点 `{top.path}`：{top.suggestions[0] if top.suggestions else '评估拆分'}")
    actions.append("将 `git-arch analyze --incremental` 接入日常/CI，监控新增拐点。")
    actions.append("对 Top 热点建立测试覆盖基线后再进行结构性修改。")
    return actions
