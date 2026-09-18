from __future__ import annotations

from git_arch.config.schema import AppConfig
from git_arch.detect.merge import merge_changepoints
from git_arch.detect.pelt import detect_changepoints
from git_arch.models import ChangePoint, DecayEvent, TimeSeries


def run_detection(series_list: list[TimeSeries], cfg: AppConfig) -> tuple[list[ChangePoint], list[DecayEvent]]:
    cps: list[ChangePoint] = []
    for ts in series_list:
        if ts.entity_kind == "class":
            continue
        cps.extend(detect_changepoints(ts, cfg))
    events = merge_changepoints(cps)
    return cps, events
