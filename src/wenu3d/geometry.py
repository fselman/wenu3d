from __future__ import annotations
import numpy as np


def unit(vector) -> np.ndarray:
    v = np.asarray(vector, dtype=float)
    if v.size == 0 or not np.all(np.isfinite(v)):
        raise ValueError("Vector components must be finite.")
    n = np.linalg.norm(v)
    if n == 0:
        raise ValueError("Cannot normalize the zero vector.")
    return v / n
