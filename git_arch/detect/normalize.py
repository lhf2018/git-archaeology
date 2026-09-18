from __future__ import annotations

import numpy as np


def zscore(values: list[float]) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return arr
    std = arr.std()
    if std < 1e-12:
        return np.zeros_like(arr)
    return (arr - arr.mean()) / std


def minmax(values: list[float]) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    lo, hi = arr.min(initial=0.0), arr.max(initial=0.0)
    if hi - lo < 1e-12:
        return np.zeros_like(arr)
    return (arr - lo) / (hi - lo)
