from __future__ import annotations

from git_arch.attribute.anonymize import anonymize_author
from git_arch.detect.normalize import zscore
from git_arch.detect.severity import score_to_severity
from git_arch.detect.threshold import threshold_detect
from git_arch.git.history import _normalize_numstat_path
from git_arch.git.parse import is_fix_commit
from git_arch.metrics.base import entropy_normalized, gini
from git_arch.metrics.complexity import analyze_complexity


def test_entropy_single_author():
    h, n = entropy_normalized({"a@x": 10})
    assert n == 1
    assert h == 0.0


def test_entropy_even_two():
    h, n = entropy_normalized({"a": 5, "b": 5})
    assert n == 2
    assert abs(h - 1.0) < 1e-9


def test_gini_equal():
    assert abs(gini({"a": 5, "b": 5})) < 1e-9


def test_zscore_constant():
    import numpy as np

    z = zscore([3.0, 3.0, 3.0])
    assert np.allclose(z, 0)


def test_severity():
    assert score_to_severity(3.0) == "high"
    assert score_to_severity(1.0) == "medium"
    assert score_to_severity(0.1) == "low"


def test_fix_commit():
    assert is_fix_commit("fix: crash on null")
    assert is_fix_commit("Revert bad merge")
    assert not is_fix_commit("feat: add login")


def test_anonymize_stable():
    a = anonymize_author("Alice@Example.com")
    b = anonymize_author("alice@example.com")
    assert a == b
    assert a.startswith("Contributor#")


def test_analyze_complexity_python():
    src = """
def a(x):
    if x:
        return 1
    elif x == 2:
        return 2
    else:
        return 3

def b(y):
    for i in y:
        if i:
            pass
"""
    v = analyze_complexity(src, "sample.py", "sum")
    assert v >= 2


def test_normalize_rename_removed_dir():
    raw = "aurora-server/src/main/java/com/lhf/{mix => }/experiment/ExperimentService.java"
    assert (
        _normalize_numstat_path(raw)
        == "aurora-server/src/main/java/com/lhf/experiment/ExperimentService.java"
    )


def test_threshold_detect_spike():
    import numpy as np

    signal = np.array([0.0] * 10 + [5.0] * 10)
    idxs = threshold_detect(signal, window=2, tau=1.0)
    assert any(8 <= i <= 12 for i in idxs)
