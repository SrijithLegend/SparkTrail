"""Load a YAML scenario -> objects, run the fixed-step loop, return the trace.

Builds any charger type (§1.1) behind any microgrid type (§1.2) from the
registries, with the injector, BMS, hub controller, and an optional
physics-aware monitor. New plugin types need only a registry entry.
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
from ..control.proxy import PhysicsProxy
from ..monitor.physics_aware import PhysicsAwareMonitor
from ..monitor.sensor_fusion import SensorFusionValidator
from ..physics.battery_thermal import BatteryThermal
from ..physics.feeder import Feeder
from ..scoring import impact
from ..targets.charger import Charger, CHARGER_SPECS
from ..targets.microgrid import Microgrid, GRID_SPECS
from dataclasses import replace


def load(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run(cfg: dict) -> dict:
    store = EventStore()
    attacks = [Attack(**a) for a in cfg.get("attacks", [])]
    inj = Injector(attacks, store)

    ambient = cfg.get("ambient_C", 35.0)
    tcfg = cfg["target"]
    ctype = tcfg["type"]
    if ctype not in CHARGER_SPECS:
        raise ValueError(f"unknown charger type {ctype!r}; known: {list(CHARGER_SPECS)}")
    spec = CHARGER_SPECS[ctype]
    pack = tcfg.get("pack", {})
    limits = tcfg.get("limits", {})
    spec = replace(spec,
                   C=pack.get("C", spec.C), R=pack.get("R", spec.R),
                   cool_low=pack.get("cool_low", spec.cool_low),
                   cool_high=pack.get("cool_high", spec.cool_high),
                   normal_A=limits.get("normal_A", spec.normal_A),
                   max_A=limits.get("max_A", spec.max_A))

    # Phase 1: optional zero-trust physics proxy (defends over-limit commands)
    pcfg = cfg.get("proxy")
    proxy = None
    if pcfg:
        pc = pcfg if isinstance(pcfg, dict) else {}
        proxy = PhysicsProxy(
            thermal_limit_A=pc.get("thermal_limit_A", round(spec.normal_A * 1.2, 1)),
            grid_max_kW=pc.get("grid_max_kW", 500.0),
            v_min_pu=pc.get("v_min_pu", 0.94))

    hcfg = cfg.get("hub", {})
    n = hcfg.get("chargers", 1)
    chargers = [Charger(f"charger_{i+1:02d}", store, inj, spec, ambient, proxy=proxy) for i in range(n)]

    gtype = hcfg.get("grid_type", "single_feeder")
    if gtype not in GRID_SPECS:
        raise ValueError(f"unknown grid type {gtype!r}; known: {list(GRID_SPECS)}")
    grid = Microgrid(
        name="hub_tx", store=store, injector=inj, spec=GRID_SPECS[gtype],
        feeder=Feeder(S_rated_kVA=hcfg.get("transformer_kVA", 500.0),
                      Z_pu=hcfg.get("impedance_pu", 0.05)),
        controller=HubController(), chargers=chargers,
        pv_kW=hcfg.get("pv_kW", 0.0), S_base_kVA=hcfg.get("transformer_kVA", 500.0),
        inertia_H=hcfg.get("inertia_H", 4.0), proxy=proxy)

    mon = None
    mcfg = cfg.get("monitor", {}).get("physics_aware")
    if mcfg:
        mm = mcfg.get("model", {})
        mon = PhysicsAwareMonitor(
            store, node=chargers[0].name, divergence_C=mcfg.get("divergence_C", 3.0),
            model=BatteryThermal(C=mm.get("C", 430_000.0), R=mm.get("R", 0.11),
                                 T_ambient=ambient, T=ambient))

    # Phase 2: cross-layer sensor fusion validator (on by default; alerts only)
    fusion = None
    if cfg.get("fusion", True):
        fusion = SensorFusionValidator(store, node=chargers[0].name, R=spec.R, C_th=spec.C,
                                       h=spec.cool_high, T_amb=ambient,
                                       min_load_A=max(50.0, spec.normal_A * 0.5))

    dt = cfg.get("dt_s", 1.0)
    run_s = cfg.get("run_s", 2400)

    def on_step(i, t):
        for c in chargers:
            c.step(dt, t)
        grid.step(dt, t)
        c0 = chargers[0]
        if mon:
            mon.step(dt, t, c0.current_A, c0.reported_T, c0.cooling_on)
        if fusion:
            fusion.step(dt, t, c0.current_A, spec.voltage_V, c0.reported_T,
                        cause=inj.cause_for("sensor.pack_temp_C"))

    clock.run(int(run_s / dt), dt, on_step)

    events = store.all()
    return {
        "name": cfg.get("name", "scenario"),
        "charger_type": spec.kind,
        "grid_type": GRID_SPECS[gtype].kind,
        "ambient_C": ambient,
        "run_s": run_s,
        "events": store.to_json(),
        "node_depths": store.node_depths(),
        "score": impact.score(events),
    }


def run_file(path: str | Path) -> dict:
    return run(load(path))
