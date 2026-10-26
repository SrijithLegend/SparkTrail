"""Hub site controller: broadcasts a per-charger current setpoint and issues
load-shed when feeder load exceeds a ceiling. An attack can override the
broadcast (mass_command) or drop the load-shed signal (dos_blackhole).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HubController:
    shed_above_pct: float = 100.0   # request load-shed when feeder load exceeds this
    shed_factor: float = 0.5        # cut each charger to this fraction when shedding

    def decide(self, feeder_load_pct: float) -> float:
        """Return a multiplier each charger should apply to its limit."""
        return self.shed_factor if feeder_load_pct > self.shed_above_pct else 1.0
