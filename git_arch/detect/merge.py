from __future__ import annotations

from collections import defaultdict

from git_arch.detect.severity import max_severity
from git_arch.models import ChangePoint, DecayEvent


def merge_changepoints(cps: list[ChangePoint]) -> list[DecayEvent]:
    """Merge change points that share the same commit into decay events."""
    by_commit: dict[str, list[ChangePoint]] = defaultdict(list)
    for cp in cps:
        by_commit[cp.commit_sha].append(cp)

    events: list[DecayEvent] = []
    for sha, group in by_commit.items():
        sev = group[0].severity
        for cp in group[1:]:
            sev = max_severity(sev, cp.severity)
        entities = sorted({cp.entity_id for cp in group})
        events.append(
            DecayEvent(
                commit_sha=sha,
                timestamp=group[0].timestamp,
                entity_ids=entities,
                change_points=group,
                hypothesis_id=None,
                hypothesis_label="",
                causal_chain="",
                severity=sev,
            )
        )
    events.sort(key=lambda e: (e.timestamp, e.commit_sha))
    return events
