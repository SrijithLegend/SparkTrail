"""DC-fast charger (P0): richest physics, clearest attack-to-impact story.

Wires: backend_link -> limit_A command ; sensor_bus -> pack temp reading.
The charger passes both through the Injector so command_override and
sensor_spoof take effect at the modelled link, then runs the BMS (on the
*reported* temp) and the battery thermal plant (on the *true* temp).
"""
from __future__ import annotations

from ..control.bms import BMS
from ..core.events import Event, EventStore
from ..physics.battery_thermal import BatteryThermal
from ..attacks.injector import Injector


class ChargerDCFast:
    def __init__(self, name: str, store: EventStore, injector: Injector,
                 plant: BatteryThermal, bms: BMS,
                 normal_A: float = 125.0, max_A: float = 250.0,
                 voltage_V: float = 400.0) -> None:
        self.name = name
        self.store = store
        self.inj = injector
        self.plant = plant
        self.bms = bms
        self.base_limit_A = normal_A
        self.max_A = max_A
        self.voltage_V = voltage_V
        self._limit_A = normal_A
        self.current_A = 0.0
        self.hub_multiplier = 1.0   # set by hub controller / load-shed
        self.reported_T = plant.T   # last temp the controller saw (for the monitor)
        self.cooling_on = False

    def apply_command(self, field: str, value) -> None:
        if field == "charging_profile.limit_A" and value is not None:
            self._limit_A = value

    def read(self) -> dict:
        return {"pack_temp_C": self.plant.T}  # pre-spoof; spoof applied in step

    def true_state(self) -> dict:
        return {"pack_temp_C": self.plant.T, "current_A": self.current_A}

    def power_kW(self) -> float:
        return self.current_A * self.voltage_V / 1000.0

    def step(self, dt: float, t: float) -> list[Event]:
        evs: list[Event] = []

        # 1. backend link: the commanded current limit (attack may override it)
        cmd = self.inj.transform_command(
            "charging_profile.limit_A", self.base_limit_A, t, node=self.name)
        if cmd is not None:
            self._limit_A = cmd
        limit = min(self._limit_A, self.max_A) * self.hub_multiplier

        # 2. sensor bus: temperature the controller sees (attack may spoof it)
        true_T = self.plant.T
        reported_T = self.inj.transform_reading("sensor.pack_temp_C", true_T, t)

        # 3. BMS decides from the REPORTED temperature
        allowed_A, cooling_on = self.bms.decide(reported_T, limit)
        self.current_A = allowed_A
        self.reported_T = reported_T
        self.cooling_on = cooling_on

        # 4. plant advances on the TRUE physics
        new_T = self.plant.step(dt, allowed_A, cooling_on)

        cause = self.inj.cause_for("charging_profile.limit_A") or \
            self.inj.cause_for("sensor.pack_temp_C")
        evs.append(self.store.add(
            t=t, layer="control", node=self.name, kind="command",
            field="current_A", value=round(allowed_A, 1), caused_by=cause))
        evs.append(self.store.add(
            t=t, layer="physics", node=self.name, kind="state",
            field="pack_temp_C", value=round(new_T, 2), caused_by=cause))
        if reported_T != true_T:
            evs.append(self.store.add(
                t=t, layer="cyber", node=self.name, kind="reading",
                field="reported_temp_C", value=round(reported_T, 2),
                caused_by=self.inj.cause_for("sensor.pack_temp_C"),
                flag="illustrative"))
        return evs
