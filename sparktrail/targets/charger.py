"""All EV charger types as ONE parametrized plugin (ladder: don't write six
near-identical classes). A ChargerSpec sets the power band, thermal params and
which characteristic state a type carries (coolant loop for HPC, buffer for a
battery-buffered unit, export for V2G). The physics and attack wiring are shared.

Links wired here:
  cyber.backend_link  -> charging_profile.limit_A   (command_override / mass_command / replay)
  cyber.vehicle_link  -> vehicle.requested_A         (command_override: EV asks for more)
  cyber.sensor_bus    -> sensor.pack_temp_C          (sensor_spoof)
  cyber.firmware_state-> firmware.thermal_cutoff      (command_override: disable the cutoff)
"""
from __future__ import annotations

from dataclasses import dataclass

from ..control.bms import BMS
from ..core.events import Event, EventStore
from ..physics.battery_thermal import BatteryThermal
from ..attacks.injector import Injector


@dataclass
class ChargerSpec:
    kind: str
    normal_A: float
    max_A: float
    voltage_V: float
    R: float
    C: float
    cool_low: float
    cool_high: float
    has_coolant: bool = False      # HPC: liquid-cooled cable/pack -> coolant_temp_C
    has_buffer: bool = False       # battery-buffered: local storage -> buffer_soc/temp
    bidirectional: bool = False    # V2G: can export -> export_power_kW


# §1.1 taxonomy. temp/current modelled for every type; the lumped thermal form
# scales naturally with power, so a 2 kW AC unit barely warms and an HPC runs hot.
CHARGER_SPECS: dict[str, ChargerSpec] = {
    "charger_ac1":      ChargerSpec("AC Level 1", 10, 16, 230, 0.8, 60_000, 20, 40),
    "charger_ac2":      ChargerSpec("AC Level 2", 32, 48, 400, 0.5, 90_000, 40, 90),
    "charger_dcfast":   ChargerSpec("DC fast", 125, 250, 400, 0.10, 450_000, 150, 300),
    "charger_hpc":      ChargerSpec("DC ultra-fast / HPC", 350, 500, 920, 0.06, 600_000, 300, 900, has_coolant=True),
    "charger_buffered": ChargerSpec("Battery-buffered", 125, 250, 400, 0.10, 450_000, 150, 300, has_buffer=True),
    "charger_v2g":      ChargerSpec("Bidirectional / V2G", 63, 120, 400, 0.12, 400_000, 120, 260, bidirectional=True),
}


class Charger:
    def __init__(self, name: str, store: EventStore, injector: Injector,
                 spec: ChargerSpec, ambient_C: float, bms: BMS | None = None) -> None:
        self.name = name
        self.store = store
        self.inj = injector
        self.spec = spec
        self.bms = bms or BMS()
        self.plant = BatteryThermal(C=spec.C, R=spec.R, cool_low=spec.cool_low,
                                    cool_high=spec.cool_high, T_ambient=ambient_C, T=ambient_C)
        self.amb = ambient_C
        self.base_limit_A = spec.normal_A
        self._limit_A = spec.normal_A
        self.current_A = 0.0
        self.hub_multiplier = 1.0
        self.reported_T = ambient_C
        self.cooling_on = False
        self.thermal_cutoff = True          # firmware flag; an attack can disable it
        # coolant loop (HPC): a second thermal node between pack and ambient
        self.coolant_T = ambient_C
        self.C_cool, self.k_pc, self.h_rad = 200_000.0, 400.0, 500.0
        # buffer (battery-buffered)
        self.buffer_soc = 100.0
        # export (V2G)
        self.export_kW = 0.0

    def apply_command(self, field: str, value) -> None:
        if value is None:
            return
        if field == "charging_profile.limit_A":
            self._limit_A = value
        elif field == "firmware.thermal_cutoff":
            self.thermal_cutoff = bool(value)

    def read(self) -> dict:
        return {"pack_temp_C": self.plant.T}

    def true_state(self) -> dict:
        return {"pack_temp_C": self.plant.T, "current_A": self.current_A,
                "coolant_temp_C": self.coolant_T}

    def power_kW(self) -> float:
        return abs(self.current_A) * self.spec.voltage_V / 1000.0

    def step(self, dt: float, t: float) -> list[Event]:
        evs: list[Event] = []
        s = self.spec

        # backend link: commanded current limit (may be overridden/replayed/mass-commanded)
        cmd = self.inj.transform_command("charging_profile.limit_A", self.base_limit_A, t, node=self.name)
        if cmd is not None:
            self._limit_A = cmd
        # vehicle link: EV's requested current (may be spoofed high)
        req = self.inj.transform_command("vehicle.requested_A", s.max_A, t, node=self.name)
        # firmware link: thermal cutoff enable flag (may be disabled)
        self.thermal_cutoff = bool(self.inj.transform_command(
            "firmware.thermal_cutoff", True, t, node=self.name))

        limit = min(self._limit_A, s.max_A, req if req is not None else s.max_A) * self.hub_multiplier

        # sensor bus: temperature the controller sees (may be spoofed)
        true_T = self.plant.T
        reported_T = self.inj.transform_reading("sensor.pack_temp_C", true_T, t)

        allowed_A, cooling_on = self.bms.decide(reported_T, limit)
        if not self.thermal_cutoff:
            # cutoff disabled: the hard stop at cutoff_C no longer applies
            allowed_A = max(allowed_A, limit if reported_T < self.bms.derate_C else allowed_A)
        self.current_A = -allowed_A if (s.bidirectional and req is not None and req < 0) else allowed_A
        self.reported_T, self.cooling_on = reported_T, cooling_on

        # pack thermal: reject to coolant (HPC) or straight to ambient
        if s.has_coolant:
            new_T = self.plant.step(dt, allowed_A, cooling_on, sink_T=self.coolant_T)
            q_in = self.k_pc * (self.plant.T - self.coolant_T)
            q_out = self.h_rad * (self.coolant_T - self.amb)
            self.coolant_T += (q_in - q_out) / self.C_cool * dt
        else:
            new_T = self.plant.step(dt, allowed_A, cooling_on)

        cause = self.inj.cause_for("charging_profile.limit_A") or \
            self.inj.cause_for("vehicle.requested_A") or \
            self.inj.cause_for("firmware.thermal_cutoff") or \
            self.inj.cause_for("sensor.pack_temp_C")

        evs.append(self.store.add(t=t, layer="control", node=self.name, kind="command",
                                  field="current_A", value=round(self.current_A, 1), caused_by=cause))
        evs.append(self.store.add(t=t, layer="physics", node=self.name, kind="state",
                                  field="pack_temp_C", value=round(new_T, 2), caused_by=cause))
        if s.has_coolant:
            evs.append(self.store.add(t=t, layer="physics", node=self.name, kind="state",
                                      field="coolant_temp_C", value=round(self.coolant_T, 2), caused_by=cause))
        if s.has_buffer:
            self.buffer_soc = max(0.0, self.buffer_soc - self.power_kW() * dt / 3600.0 / 1.0)
            evs.append(self.store.add(t=t, layer="physics", node=self.name, kind="state",
                                      field="buffer_soc", value=round(self.buffer_soc, 1), caused_by=cause))
        if s.bidirectional and self.current_A < 0:
            self.export_kW = self.power_kW()
            evs.append(self.store.add(t=t, layer="physics", node=self.name, kind="state",
                                      field="export_power_kW", value=round(self.export_kW, 1), caused_by=cause))
        if reported_T != true_T:
            evs.append(self.store.add(t=t, layer="cyber", node=self.name, kind="reading",
                                      field="reported_temp_C", value=round(reported_T, 2),
                                      caused_by=self.inj.cause_for("sensor.pack_temp_C"), flag="illustrative"))
        return evs
