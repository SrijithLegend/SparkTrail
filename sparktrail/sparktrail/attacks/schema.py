"""The §2 attack object: a declarative 'wrong value on a link at time T'.

Models behaviour, not exploitation. No access/how-to detail by design.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

ENTRY_POINTS = {
    "cyber.backend_link", "cyber.vehicle_link", "cyber.sensor_bus",
    "cyber.hub_controller", "cyber.inverter_link", "cyber.firmware_state",
}
MECHANISMS = {
    "command_override", "sensor_spoof", "setpoint_drift", "replay",
    "mass_command", "desync", "dos_blackhole",
}


@dataclass
class Attack:
    id: str
    entry_point: str
    mechanism: str
    field: str
    start_s: float = 0.0
    to: Optional[float] = None          # command_override / mass_command target
    hold_value: Optional[float] = None  # sensor_spoof frozen value
    rate_per_s: Optional[float] = None  # setpoint_drift
    delay_s: Optional[float] = None     # desync: how late the message arrives
    end_s: Optional[float] = None
    targets: Optional[list[str]] = None # mass_command fan-out; None = all

    def __post_init__(self) -> None:
        if self.entry_point not in ENTRY_POINTS:
            raise ValueError(f"unknown entry_point {self.entry_point!r}")
        if self.mechanism not in MECHANISMS:
            raise ValueError(f"unknown mechanism {self.mechanism!r}")

    def active(self, t: float) -> bool:
        if t < self.start_s:
            return False
        return self.end_s is None or t <= self.end_s
