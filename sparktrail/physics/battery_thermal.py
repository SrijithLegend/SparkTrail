"""Lumped single-temperature battery thermal model (P0).

    dT/dt = ( I^2*R - h*(T - T_ambient) ) / C

Simple and defensible. Swap for a PyBaMM adapter later; keep the interface.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BatteryThermal:
    C: float = 450_000.0        # lumped heat capacity (J/K)
    R: float = 0.10             # effective internal resistance (ohm)
    cool_low: float = 150.0     # h (W/K) when BMS cooling idle
    cool_high: float = 300.0    # h (W/K) when BMS cooling active
    T_ambient: float = 35.0     # Chennai afternoon
    T: float = 35.0             # current true temperature (deg C)

    def step(self, dt: float, current_A: float, cooling_on: bool) -> float:
        h = self.cool_high if cooling_on else self.cool_low
        q_in = current_A ** 2 * self.R
        q_out = h * (self.T - self.T_ambient)
        self.T += (q_in - q_out) / self.C * dt
        return self.T
