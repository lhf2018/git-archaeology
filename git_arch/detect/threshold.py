from __future__ import annotations

import numpy as np


def threshold_detect(signal: np.ndarray, window: int = 2, tau: float = 1.0) -> list[int]:
    idxs: list[int] = []
    for i in range(window, len(signal) - window):
        left = signal[i - window : i].mean()
        right = signal[i : i + window].mean()
        if abs(right - left) >= tau:
            idxs.append(i)
    filtered: list[int] = []
    for i in idxs:
        if not filtered or i - filtered[-1] >= window:
            filtered.append(i)
    return filtered
