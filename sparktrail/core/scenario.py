"""Load a YAML scenario -> objects, run the fixed-step loop, return the trace.

Builds the P0 chain: DC-fast charger(s) -> hub feeder, with the injector,
BMS, hub controller, and an optional physics-aware monitor.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from . import clock
from .events import EventStore
from ..attacks.injector import Injector
from ..attacks.schema import Attack
from ..control.bms import BMS
from ..control.hub_controller import HubController
from ..monitor.physics_aware import PhysicsAwareMonitor
from ..physics.battery_thermal import BatteryThermal
from ..physics.feeder import Feeder
from ..scoring import impact
from ..targets.charger_dcfast import ChargerDCFast
from ..targets.hub_feeder import HubFeeder


def load(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run(cfg: dict) -> dict:
    store = EventStore()
    attacks = [Attack(**a) for a in cfg.get("attacks", [])]
    inj = Injector(attacks, store)

    ambient = cfg.get("ambient_C", 35.0)
    tcfg = cfg["target"]
    pack = tcfg.get("pack", {})
    limits = tcfg.get("limits", {})

    n = cfg.get("hub", {}).get("chargers", 1)
    chargers = []
    for i in range(n):
        plant = BatteryThermal(
            C=pack.get("C", 450_000.0), R=pack.get("R", 0.10),
            cool_low=pack.get("cool_low", 150.0), cool_high=pack.get("cool_high", 300.0),
            T_ambient=ambient, T=ambient)
        chargers.append(ChargerDCFast(
            name=f"charger_{i+1:02d}", store=store, injector=inj, plant=plant, bms=BMS(),
            normal_A=limits.get("normal_A", 125.0), max_A=limits.get("max_A", 250.0)))

    hcfg = cfg.get("hub", {})
    hub = HubFeeder(
        name="hub_tx", store=store, injector=inj,
        feeder=Feeder(S_rated_kVA=hcfg.get("transformer_kVA", 500.0),
                      Z_pu=hcfg.get("impedance_pu", 0.05)),
        controller=HubController(), chargers=chargers)

    mon = None
    mcfg = cfg.get("monitor", {}).get("physics_aware")
    if mcfg:
        mm = mcfg.get("model", {})
        mon = PhysicsAwareMonitor(
            store, node=chargers[0].name, divergence_C=mcfg.get("divergence_C", 3.0),
            model=BatteryThermal(C=mm.get("C", 430_000.0), R=mm.get("R", 0.11),
                                 T_ambient=ambient, T=ambient))

    dt = cfg.get("dt_s", 1.0)
    run_s = cfg.get("run_s", 2400)

    def on_step(i, t):
        for c in chargers:
            c.step(dt, t)
        hub.step(dt, t)
        if mon:
            c0 = chargers[0]
            mon.step(dt, t, c0.current_A, c0.reported_T, c0.cooling_on)

    clock.run(int(run_s / dt), dt, on_step)

    events = store.all()
    return {
        "name": cfg.get("name", "scenario"),
        "ambient_C": ambient,
        "run_s": run_s,
        "events": store.to_json(),
        "score": impact.score(events),
    }


def run_file(path: str | Path) -> dict:
    return run(load(path))
