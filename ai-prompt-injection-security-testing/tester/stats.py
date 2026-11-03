"""Small pure statistics helpers."""

from __future__ import annotations

from math import sqrt

Z_95 = 1.959964


def wilson_interval(successes: int, trials: int, z: float = Z_95) -> tuple:
    """Wilson score interval for a proportion, as (lower, upper)."""
    if trials < 1 or not 0 <= successes <= trials:
        raise ValueError("need trials >= 1 and 0 <= successes <= trials.")
    p = successes / trials
    denom = 1 + z * z / trials
    centre = p + z * z / (2 * trials)
    margin = z * sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials))
    return max(0.0, (centre - margin) / denom), min(1.0, (centre + margin) / denom)
