"""Physics-aware monitor (the one piece of 'defense'). ALERTS ONLY.

Runs a REDUCED thermal model off the MEASURED current and compares its
prediction to the REPORTED temperature. When they diverge beyond a threshold,
a sensor is probably lying. Its R/C/h MUST differ from the plant's, or the
detection time is fake. Detection delay is reported honestly.
"""
from __future__ import annotations

from ..core.events import Event, EventStore
from ..physics.battery_thermal import BatteryThermal


class PhysicsAwareMonitor:
    def __init__(self, store: EventStore, node: str, divergence_C: float = 3.0,
                 model: BatteryThermal | None = None) -> None:
        self.store = store
        self.node = node
        self.divergence_C = divergence_C
        # deliberately a *different* model from the plant
        self.model = model or BatteryThermal(C=430_000.0, R=0.11)
        self.alerted = False
        self.alert_t: float | None = None

    def step(self, dt: float, t: float, measured_current_A: float,
             reported_temp_C: float, cooling_on: bool) -> list[Event]:
        predicted = self.model.step(dt, measured_current_A, cooling_on)
        if self.alerted:
            return []
        if abs(predicted - reported_temp_C) > self.divergence_C:
            self.alerted = True
            self.alert_t = t
            return [self.store.add(
                t=t, layer="monitor", node=self.node, kind="alert",
                field="sensor_divergence_C", value=round(predicted - reported_temp_C, 2),
                caused_by=None)]
        return []
