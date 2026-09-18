from __future__ import annotations

from git_arch.config.schema import AppConfig
from git_arch.git.parse import is_fix_commit
from git_arch.models import CommitRef, DecayEvent, HistoryGraph


RULES = [
    ("giant_commit", "巨型提交引入复杂度跃升"),
    ("ownership_burst", "所有权突变为多人（碎片化）"),
    ("hotfix_cluster", "高频 hotfix / 修复提交集中期"),
    ("churn_spike", "改动频率与复杂度叠加恶化"),
    ("coupling_hint", "同提交触及多模块（耦合迹象）"),
]


def attribute_events(
    events: list[DecayEvent],
    graph: HistoryGraph,
    cfg: AppConfig,
) -> list[DecayEvent]:
    commit_map = {c.sha: c for c in graph.commits}
    # Precompute lines changed per commit across tracked files
    lines_by_commit: dict[str, int] = {}
    files_by_commit: dict[str, set[str]] = {}
    for path, revs in graph.files.items():
        for rev in revs:
            lines_by_commit[rev.commit_sha] = lines_by_commit.get(rev.commit_sha, 0) + (
                rev.lines_added + rev.lines_deleted
            )
            files_by_commit.setdefault(rev.commit_sha, set()).add(path)

    ordered = list(graph.commits)
    sha_to_idx = {c.sha: i for i, c in enumerate(ordered)}

    for event in events:
        commit = commit_map.get(event.commit_sha)
        event.commit_message = commit.message if commit else ""
        event.lines_changed = lines_by_commit.get(event.commit_sha, 0)
        event.author_name = commit.author_name if commit else ""
        event.author_email = commit.author_email if commit else ""

        rid, label = _match_rule(
            event, commit, ordered, sha_to_idx, files_by_commit, cfg
        )
        event.hypothesis_id = rid
        event.hypothesis_label = label
    return events


def _match_rule(
    event: DecayEvent,
    commit: CommitRef | None,
    ordered: list[CommitRef],
    sha_to_idx: dict[str, int],
    files_by_commit: dict[str, set[str]],
    cfg: AppConfig,
) -> tuple[str, str]:
    metrics = {cp.metric for cp in event.change_points}
    atr = cfg.attribution

    # R1 giant commit
    if event.lines_changed >= atr.giant_commit_lines and (
        "complexity" in metrics or "churn_complexity" in metrics
    ):
        return "giant_commit", RULES[0][1]

    # R2 ownership burst
    if "ownership_fragmentation" in metrics:
        for cp in event.change_points:
            if cp.metric == "ownership_fragmentation" and cp.delta > 0.05:
                return "ownership_burst", RULES[1][1]

    # R3 hotfix cluster
    if commit and commit.sha in sha_to_idx:
        i = sha_to_idx[commit.sha]
        w = atr.hotfix_window
        window = ordered[max(0, i - w) : i + 1]
        if window:
            ratio = sum(1 for c in window if is_fix_commit(c.message)) / len(window)
            if ratio >= atr.hotfix_ratio:
                return "hotfix_cluster", RULES[2][1]

    # R4 churn spike
    if "churn_complexity" in metrics:
        return "churn_spike", RULES[3][1]

    # R5 coupling hint
    n_files = len(files_by_commit.get(event.commit_sha, set()))
    if n_files >= 5 or len(event.entity_ids) >= 3:
        return "coupling_hint", RULES[4][1]

    # default: primary metric label
    if "complexity" in metrics:
        return "giant_commit", RULES[0][1]
    return "churn_spike", RULES[3][1]
