"""Hub transformer / feeder steady-state math (P0, algebraic).

    load_pct   = 100 * P_total / S_rated
    v_drop_pct = 100 * Z * P_total / S_rated
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Feeder:
    S_rated_kVA: float = 500.0
    Z_pu: float = 0.05

    def evaluate(self, p_total_kW: float) -> tuple[float, float]:
        load_pct = 100.0 * p_total_kW / self.S_rated_kVA
        v_drop_pct = 100.0 * self.Z_pu * p_total_kW / self.S_rated_kVA
        return load_pct, v_drop_pct
