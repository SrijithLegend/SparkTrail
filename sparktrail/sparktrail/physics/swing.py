"""Single-bus swing approximation for islanded microgrid frequency.

    df/dt = ( P_gen - P_load ) / (2*H*S_base)   [per-unit]
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Swing:
    H: float = 4.0              # inertia constant (s)
    S_base_kVA: float = 500.0
    f: float = 50.0            # Hz
    f_nominal: float = 50.0

    def step(self, dt: float, p_gen_pu: float, p_load_pu: float) -> float:
        dfdt = (p_gen_pu - p_load_pu) / (2.0 * self.H) * self.f_nominal
        self.f += dfdt * dt
        return self.f
