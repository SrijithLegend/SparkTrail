"""BMS: derating + cooling logic. Reads the (possibly spoofed) sensor temp,
not the true temp. That gap is what makes sensor-spoof attacks meaningful.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BMS:
    cool_on_C: float = 40.0     # turn cooling on above this reported temp
    derate_C: float = 50.0      # start derating current above this reported temp
    cutoff_C: float = 60.0      # hard stop (reported)

    def decide(self, reported_temp_C: float, limit_A: float) -> tuple[float, bool]:
        """Return (allowed_current_A, cooling_on) from the REPORTED temperature."""
        cooling_on = reported_temp_C >= self.cool_on_C
        if reported_temp_C >= self.cutoff_C:
            return 0.0, True
        if reported_temp_C >= self.derate_C:
            # linear derate from full at derate_C to zero at cutoff_C
            span = self.cutoff_C - self.derate_C
            frac = max(0.0, (self.cutoff_C - reported_temp_C) / span)
            return limit_A * frac, cooling_on
        return limit_A, cooling_on
