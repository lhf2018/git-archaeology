from datetime import datetime, timezone

from git_arch.models import (
    ArchaeologyReport,
    ChangePoint,
    DecayEvent,
    MetricPoint,
    TimeSeries,
)
from git_arch.metrics.classes import class_breakdown
from git_arch.report.classify import area_of, build_class_view, build_view


def test_area_of_top_module():
    assert area_of("aurora-recommendation/src/main/java/A.java") == "aurora-recommendation"
    assert area_of("App.tsx") == "App.tsx"


def test_build_view_groups_files_and_keeps_author():
    ts = datetime(2026, 8, 15, tzinfo=timezone.utc)
    event = DecayEvent(
        commit_sha="abc1234def",
        timestamp=ts,
        entity_ids=["aurora-infrastructure/src/main/java/com/lhf/graph/GraphRunner.java"],
        change_points=[
            ChangePoint(
                entity_id="aurora-infrastructure/src/main/java/com/lhf/graph/GraphRunner.java",
                metric="complexity",
                commit_sha="abc1234def",
                timestamp=ts,
                before_value=12,
                after_value=47,
                delta=35,
                confidence=0.9,
                severity="high",
            ),
            ChangePoint(
                entity_id="aurora-infrastructure/src",
                metric="churn_complexity",
                commit_sha="abc1234def",
                timestamp=ts,
                before_value=1,
                after_value=9,
                delta=8,
                confidence=0.5,
                severity="low",
            ),
        ],
        hypothesis_id="giant_commit",
        hypothesis_label="巨型提交",
        causal_chain="ignored",
        severity="high",
        commit_message="feat: parallel DAG",
        author_name="Ada Lovelace",
    )
    series = TimeSeries(
        entity_id="aurora-infrastructure/src/main/java/com/lhf/graph/GraphRunner.java",
        entity_kind="file",
        metric="complexity",
        points=[
            MetricPoint("a", ts, 12),
            MetricPoint("b", ts, 47),
        ],
    )
    report = ArchaeologyReport(
        meta={},
        summary={},
        global_series=[series],
        events=[event],
        hotspots=[],
        actions=[],
        appendix={},
    )
    view = build_view(report)
    assert len(view["areas"]) == 1
    area = view["areas"][0]
    assert area["name"] == "aurora-infrastructure"
    assert area["changes"][0]["author"] == "Ada Lovelace"
    assert area["changes"][0]["kind"] == "复杂度"
    assert area["changes"][0]["file"] == "GraphRunner.java"
    assert area["chart"]["values"] == [12, 47]


def test_class_breakdown_groups_methods():
    src = """
class Alpha {
  int a(int x) { if (x > 0) return 1; return 0; }
}
class Beta {
  int b(int x) {
    if (x > 0) {
      if (x > 2) return 2;
      return 1;
    }
    return 0;
  }
}
"""
    classes = {c["name"]: c for c in class_breakdown(src, "Sample.java")}
    assert "Alpha" in classes
    assert "Beta" in classes
    assert classes["Alpha"]["methods"] >= 1
    assert classes["Beta"]["complexity"] >= classes["Alpha"]["complexity"]


def test_class_view_splits_multi_and_single():
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    t1 = datetime(2026, 2, 1, tzinfo=timezone.utc)

    def series(name, values):
        return TimeSeries(
            entity_id=f"mod/A.java#{name}",
            entity_kind="class",
            metric="class_complexity",
            points=[
                MetricPoint("aaa", t0, values[0], {"author": "Ann", "message": "init", "methods": 1}),
                MetricPoint("bbb", t1, values[1], {"author": "Ann", "message": "grow two", "methods": 2}),
            ],
        )

    report = ArchaeologyReport(
        meta={},
        summary={},
        global_series=[series("Alpha", [2, 10]), series("Beta", [1, 8]), series("Quiet", [3, 3])],
        events=[],
        hotspots=[],
        actions=["优先处理 high 拐点"],
        appendix={},
    )
    view = build_class_view(report)
    assert view["multi_total"] == 1
    assert view["multi"][0]["class_count"] == 2
    assert view["multi"][0]["author"] == "Ann"
    assert view["multi"][0]["total_delta"] > 0
    names = {c["name"] for c in view["multi"][0]["classes"]}
    assert names == {"Alpha", "Beta"}
    assert view["single_total"] == 2
    assert view["single"][0]["name"] == "Alpha"
    assert "jump_index" in view["single"][0]["chart"]
    assert view["single"][0]["chart"]["points"]
    assert view["single"][0]["authors"] == ["Ann"]

    from git_arch.report.classify import build_summary

    summary = build_summary(report, [], view)
    assert summary["multi_total"] == 1
    assert summary["single_total"] == 2
    assert summary["conclusions"]
    assert summary["actions"] == ["优先处理 high 拐点"]

