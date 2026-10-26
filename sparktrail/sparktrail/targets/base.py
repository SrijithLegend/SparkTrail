"""Target interface every plugin honours. Keeping true_state separate from
read() is what makes sensor-spoof attacks meaningful.
"""
from __future__ import annotations

from typing import Protocol

from ..core.events import Event


class Target(Protocol):
    name: str

    def read(self) -> dict: ...                    # sensor readings (may be altered upstream)
    def apply_command(self, field: str, value) -> None: ...
    def step(self, dt: float, t: float) -> list[Event]: ...  # advance physics, emit events
    def true_state(self) -> dict: ...              # ground truth (never seen by control/monitor)
