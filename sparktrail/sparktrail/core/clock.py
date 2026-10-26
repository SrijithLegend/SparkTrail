"""Fixed-step sim loop. dt = 1 s default."""
from __future__ import annotations

from typing import Callable


def run(steps: int, dt: float, on_step: Callable[[int, float], None]) -> None:
    """Call on_step(i, t) for each tick. Plant/control/attacks hook in via on_step."""
    for i in range(steps):
        on_step(i, i * dt)
