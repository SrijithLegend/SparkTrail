"""Single-feeder charging hub (P0): N chargers behind one transformer.

Sums charger power, evaluates the feeder, and runs load-shed via the hub
controller. A dos_blackhole on the load-shed signal keeps the multiplier at
1.0 during overload (the load-shed-suppression attack).
"""
from __future__ import annotations

from ..control.hub_controller import HubController
from ..core.events import Event, EventStore
from ..physics.feeder import Feeder
from ..attacks.injector import Injector


class HubFeeder:
    def __init__(self, name: str, store: EventStore, injector: Injector,
                 feeder: Feeder, controller: HubController,
                 chargers: list) -> None:
        self.name = name
        self.store = store
        self.inj = injector
        self.feeder = feeder
        self.controller = controller
        self.chargers = chargers
        self.load_pct = 0.0
        self.v_drop_pct = 0.0
        self._mult = 1.0

    def step(self, dt: float, t: float) -> list[Event]:
        p_total = sum(c.power_kW() for c in self.chargers)
        self.load_pct, self.v_drop_pct = self.feeder.evaluate(p_total)

        # load-shed decision; the signal crosses cyber.hub_controller and may be dropped
        want = self.controller.decide(self.load_pct)
        signal = self.inj.transform_command("hub.load_shed", want, t, node=self.name)
        self._mult = signal if signal is not None else 1.0
        for c in self.chargers:
            c.hub_multiplier = self._mult

        cause = self.inj.cause_for("hub.load_shed")
        bus_v_pct = 100.0 - self.v_drop_pct   # bus voltage as % of nominal
        evs = [
            self.store.add(
                t=t, layer="physics", node=self.name, kind="state",
                field="transformer_load_pct", value=round(self.load_pct, 1),
                caused_by=cause),
            self.store.add(
                t=t, layer="physics", node=self.name, kind="state",
                field="bus_voltage_pct", value=round(bus_v_pct, 1),
                caused_by=cause),
        ]
        if bus_v_pct < 94.0:   # IEC-style -6% undervoltage flag
            evs.append(self.store.add(
                t=t, layer="physics", node=self.name, kind="alert",
                field="undervoltage", value=round(bus_v_pct, 1), caused_by=cause))
        if self.load_pct > 100.0:
            evs.append(self.store.add(
                t=t, layer="physics", node=self.name, kind="alert",
                field="overload", value=round(self.load_pct, 1), caused_by=cause))
        return evs
