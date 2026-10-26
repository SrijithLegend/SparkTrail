"""Phase 2 — Cross-Layer Sensor Fusion Validator.

Cross-references the ELECTRICAL layer against the THERMAL layer. Joule heating
is physics the attacker cannot rewrite: current I through resistance R for dt
seconds *must* deposit I²R·dt joules, raising the pack temperature by

    dT_expected = (I² R) dt / C_th

If the reported temperature barely moves while the (hard-to-fake) current sensor
shows real load, the thermal sensor is being spoofed. We flag disagreement
beyond `tolerance` (default 15%). Cooling is ignored on the expected side, so
the check is conservative: it only fires when a sensor *under-reports* a real
rise — exactly the spoof-low case that blinds the BMS.

This is a different detector from the physics-aware monitor (which runs a full
reduced thermal model); fusion needs no model, just the energy balance. Alerts
only — it never blocks. Emits `monitor / fusion_alert`, once.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..core.events import Event, EventStore


@dataclass
class SensorFusionValidator:
    store: EventStore
    node: str = "PACK"
    R: float = 0.10            # effective resistance, ohm
    C_th: float = 4.5e5        # thermal mass, J/K
    h: float = 300.0           # cooling coeff (W/K) — use the plant's MAX, so the
                               # check is conservative: an honest pack (even cooling
                               # hard, even at thermal equilibrium) never flags.
    T_amb: float = 35.0        # ambient (deg C)
    tolerance: float = 0.15    # gap must exceed 15% of the raw Joule heating
    min_load_A: float = 80.0   # only judge when there is real load to heat the pack
    persist: int = 3           # consecutive violations (debounce a current step-change)

    def __post_init__(self) -> None:
        self._last_temp: float | None = None
        self._streak = 0
        self.alerted = False
        self.alert_t: float | None = None

    def step(self, dt: float, t: float, current_A: float, voltage_V: float,
             reported_temp_C: float, cause=None) -> list[Event]:
        prev = self._last_temp
        self._last_temp = reported_temp_C
        if self.alerted or prev is None or dt <= 0:
            return []
        reported_dT = reported_temp_C - prev
        joule = (current_A ** 2 * self.R) * dt / self.C_th
        # energy balance incl. max cooling, evaluated at the REPORTED temp the
        # attacker controls: a held-low sensor makes (T_rep - T_amb) small so the
        # model still expects a big rise, while the reported rise is ~0.
        expected_dT = joule - self.h * (prev - self.T_amb) * dt / self.C_th
        if current_A < self.min_load_A or voltage_V <= 0 or joule <= 1e-6:
            self._streak = 0
            return []
        residual = expected_dT - reported_dT      # positive => under-reported rise
        if residual <= self.tolerance * joule:
            self._streak = 0
            return []
        self._streak += 1
        if self._streak >= self.persist:
            self.alerted = True
            self.alert_t = t
            return [self.store.add(
                t=t, layer="monitor", node=self.node, kind="fusion_alert",
                field="sensor_fusion_error_pct", value=round(residual / joule * 100, 1),
                caused_by=cause, flag="modelled")]
        return []
