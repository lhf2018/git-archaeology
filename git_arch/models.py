from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

Severity = Literal["low", "medium", "high"]
EntityKind = Literal["file", "module", "class"]


@dataclass
class CommitRef:
    sha: str
    timestamp: datetime
    message: str
    author_name: str
    author_email: str
    parents: list[str] = field(default_factory=list)
    is_merge: bool = False


@dataclass
class FileRevision:
    path: str
    blob_hash: str
    commit_sha: str
    lines_added: int = 0
    lines_deleted: int = 0


@dataclass
class HistoryGraph:
    commits: list[CommitRef]
    files: dict[str, list[FileRevision]]
    path_filter: str | None = None
    branch: str = "HEAD"
    since: datetime | None = None
    until: datetime | None = None
    truncated: bool = False


@dataclass
class MetricPoint:
    commit_sha: str
    timestamp: datetime
    value: float
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class TimeSeries:
    entity_id: str
    entity_kind: EntityKind
    metric: str
    points: list[MetricPoint] = field(default_factory=list)


@dataclass
class ChangePoint:
    entity_id: str
    metric: str
    commit_sha: str
    timestamp: datetime
    before_value: float
    after_value: float
    delta: float
    confidence: float
    severity: Severity


@dataclass
class DecayEvent:
    commit_sha: str
    timestamp: datetime
    entity_ids: list[str]
    change_points: list[ChangePoint]
    hypothesis_id: str | None
    hypothesis_label: str
    causal_chain: str
    severity: Severity
    commit_message: str = ""
    lines_changed: int = 0
    author_name: str = ""
    author_email: str = ""


@dataclass
class HotspotProfile:
    path: str
    current_metrics: dict[str, float]
    series: list[TimeSeries]
    events: list[DecayEvent]
    suggestions: list[str]


@dataclass
class ArchaeologyReport:
    meta: dict[str, Any]
    summary: dict[str, Any]
    global_series: list[TimeSeries]
    events: list[DecayEvent]
    hotspots: list[HotspotProfile]
    actions: list[str]
    appendix: dict[str, Any]
