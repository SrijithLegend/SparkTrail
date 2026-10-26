"""All microgrid / grid-side types as ONE parametrized plugin (§1.2).

Composes the steady-state feeder (load %, voltage) with, for the islanded and
BESS types, the single-bus swing model (frequency). PV and BESS are optional
power sources. Load-shed control is shared.

Links wired here:
  cyber.hub_controller -> hub.load_shed            (dos_blackhole / desync)
  cyber.inverter_link  -> inverter.freq_setpoint_Hz (command_override -> freq push, §2.3 #7)
  cyber.inverter_link  -> inverter.v_setpoint_pu    (setpoint_drift  -> overvoltage, §2.3 #6)

Physical effects: transformer_load_pct, bus_voltage_pct (+ undervoltage /
overvoltage flags), and for islanded/BESS frequency_Hz + rocof_Hz_s + gen_load_pct.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..control.hub_controller import HubController
from ..core.events import Event, EventStore
from ..physics.feeder import Feeder
from ..physics.swing import Swing
from ..attacks.injector import Injector


@dataclass
class GridSpec:
    kind: str
    grid_tied: bool          # stiff external grid fixes frequency
    has_pv: bool = False
    has_bess: bool = False


GRID_SPECS: dict[str, GridSpec] = {
    "single_feeder":     GridSpec("Single-feeder hub", grid_tied=True),
    "lv_distribution":   GridSpec("LV distribution microgrid", grid_tied=True, has_pv=True),
    "islanded":          GridSpec("Islanded microgrid", grid_tied=False),
    "bess":              GridSpec("Microgrid with BESS", grid_tied=False, has_bess=True),
    "depot":             GridSpec("Campus / fleet depot", grid_tied=True),
}


class Microgrid:
    def __init__(self, name: str, store: EventStore, injector: Injector, spec: GridSpec,
                 feeder: Feeder, controller: HubController, chargers: list,
                 pv_kW: float = 0.0, S_base_kVA: float = 500.0, inertia_H: float = 4.0,
                 proxy=None) -> None:
        self.name = name
        self.store = store
        self.inj = injector
        self.spec = spec
        self.proxy = proxy          # Phase 1: zero-trust physics proxy (optional)
        self.feeder = feeder
        self.controller = controller
        self.chargers = chargers
        self.pv_kW = pv_kW
        self.S_base = S_base_kVA
        self.swing = Swing(H=inertia_H, S_base_kVA=S_base_kVA) if not spec.grid_tied else None
        self.load_pct = 0.0
        self.v_drop_pct = 0.0
        self.freq = 50.0
        self.bess_soc = 80.0
        self._mult = 1.0

    def step(self, dt: float, t: float) -> list[Event]:
        p_load = sum(c.power_kW() for c in self.chargers)
        p_net = max(0.0, p_load - (self.pv_kW if self.spec.has_pv else 0.0))
        self.load_pct, self.v_drop_pct = self.feeder.evaluate(p_net)

        # load-shed signal crosses the hub controller link (may be dropped/delayed)
        want = self.controller.decide(self.load_pct)
        signal = self.inj.transform_command("hub.load_shed", want, t, node=self.name)
        if self.proxy is not None:
            signal = self.proxy.guard_load_shed(self.store, t, self.name, want, signal,
                                                self.inj.cause_for("hub.load_shed"))
        self._mult = signal if signal is not None else 1.0
        for c in self.chargers:
            c.hub_multiplier = self._mult

        cause = self.inj.cause_for("hub.load_shed")
        evs = [self.store.add(t=t, layer="physics", node=self.name, kind="state",
                              field="transformer_load_pct", value=round(self.load_pct, 1), caused_by=cause)]

        # ---- voltage ----
        v_set = self.inj.transform_command("inverter.v_setpoint_pu", 1.0, t, node=self.name)
        inv_cause = self.inj.cause_for("inverter.v_setpoint_pu")
        if self.spec.grid_tied:
            bus_v = 100.0 - self.v_drop_pct
        else:
            # islanded: inverter regulates voltage; load droops it a few % at full load
            bus_v = (v_set if v_set is not None else 1.0) * 100.0 - 0.05 * self.load_pct
        vcause = inv_cause or cause
        evs.append(self.store.add(t=t, layer="physics", node=self.name, kind="state",
                                  field="bus_voltage_pct", value=round(bus_v, 1), caused_by=vcause))
        if bus_v < 94.0:
            evs.append(self.store.add(t=t, layer="physics", node=self.name, kind="alert",
                                      field="undervoltage", value=round(bus_v, 1), caused_by=vcause))
        if bus_v > 106.0:
            evs.append(self.store.add(t=t, layer="physics", node=self.name, kind="alert",
                                      field="overvoltage", value=round(bus_v, 1), caused_by=vcause))

        # ---- frequency (islanded / BESS only) ----
        if self.swing is not None:
            f_set = self.inj.transform_command("inverter.freq_setpoint_Hz", 50.0, t, node=self.name)
            fcause = self.inj.cause_for("inverter.freq_setpoint_Hz") or cause
            target_f = f_set if f_set is not None else 50.0
            load_pu = p_net / self.S_base
            # governor drives gen toward load, biased to hit the (possibly attacked) target
            p_gen_pu = load_pu + 0.08 * (target_f - self.freq)
            if self.spec.has_bess:
                p_bess = 0.05 * (50.0 - self.freq)        # discharge when low, charge when high
                p_gen_pu += p_bess
                self.bess_soc = max(0.0, min(100.0, self.bess_soc - p_bess * dt / 36.0))
                evs.append(self.store.add(t=t, layer="physics", node=self.name, kind="state",
                                          field="bess_soc", value=round(self.bess_soc, 1), caused_by=fcause))
            f_prev = self.freq
            self.freq = self.swing.step(dt, p_gen_pu, load_pu)
            rocof = (self.freq - f_prev) / dt
            evs.append(self.store.add(t=t, layer="physics", node=self.name, kind="state",
                                      field="frequency_Hz", value=round(self.freq, 3), caused_by=fcause))
            evs.append(self.store.add(t=t, layer="physics", node=self.name, kind="state",
                                      field="rocof_Hz_s", value=round(rocof, 4), caused_by=fcause))
            evs.append(self.store.add(t=t, layer="physics", node=self.name, kind="state",
                                      field="gen_load_pct", value=round(p_gen_pu * 100, 1), caused_by=fcause))
            if self.freq < 49.5 or self.freq > 50.5:
                evs.append(self.store.add(t=t, layer="physics", node=self.name, kind="alert",
                                          field="freq_excursion", value=round(self.freq, 3), caused_by=fcause))

        if self.load_pct > 100.0:
            evs.append(self.store.add(t=t, layer="physics", node=self.name, kind="alert",
                                      field="overload", value=round(self.load_pct, 1), caused_by=cause))
        return evs
