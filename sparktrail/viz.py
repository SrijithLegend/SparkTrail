"""Compress a run into a compact timeline the 3D scene can replay.

The raw trace is ~10k events; the scene only needs sampled node state plus the
discrete attack/alert markers. Produces a small JSON the browser embeds.
"""
from __future__ import annotations

import json
from pathlib import Path

from .core import scenario


def frames(result: dict, step_s: float = 5.0) -> dict:
    events = result["events"]
    run_s = result["run_s"]

    # latest physics state per (node, field) as we sweep time
    chargers: dict[str, dict] = {}
    hub_load = 0.0
    markers = []
    for e in events:
        if e["layer"] == "attack":
            markers.append({"t": e["t"], "type": "attack", "node": e["node"],
                            "field": e["field"], "label": str(e["value"])})
        elif e["layer"] == "monitor" and e["kind"] == "alert":
            markers.append({"t": e["t"], "type": "alert", "node": e["node"],
                            "field": e["field"], "label": "sensor divergence"})

    # build per-step snapshots by scanning events in time order
    by_t: dict[float, list] = {}
    for e in events:
        by_t.setdefault(e["t"], []).append(e)

    timeline = []
    cur_temp: dict[str, float] = {}
    cur_curr: dict[str, float] = {}
    cur_report: dict[str, float] = {}
    cur_cool: dict[str, float] = {}
    cur_load = 0.0
    cur_volt = 100.0
    cur_freq = None
    cur_bess = None
    t = 0.0
    all_t = sorted(by_t)
    ti = 0
    charger_names = sorted({e["node"] for e in events if e["node"].startswith("charger_")})
    while t <= run_s:
        while ti < len(all_t) and all_t[ti] <= t:
            for e in by_t[all_t[ti]]:
                f, v, n = e["field"], e["value"], e["node"]
                if f == "pack_temp_C": cur_temp[n] = v
                elif f == "current_A": cur_curr[n] = v
                elif f == "reported_temp_C": cur_report[n] = v
                elif f == "coolant_temp_C": cur_cool[n] = v
                elif f == "transformer_load_pct": cur_load = v
                elif f == "bus_voltage_pct": cur_volt = v
                elif f == "frequency_Hz": cur_freq = v
                elif f == "bess_soc": cur_bess = v
            ti += 1
        timeline.append({
            "t": t,
            "chargers": {n: {"temp": round(cur_temp.get(n, 35.0), 1),
                             "current": round(cur_curr.get(n, 0.0), 0),
                             "reported": round(cur_report.get(n, cur_temp.get(n, 35.0)), 1),
                             "coolant": round(cur_cool[n], 1) if n in cur_cool else None}
                         for n in charger_names},
            "load": round(cur_load, 1),
            "volt": round(cur_volt, 1),
            "freq": round(cur_freq, 3) if cur_freq is not None else None,
            "bess": round(cur_bess, 1) if cur_bess is not None else None,
        })
        t += step_s

    return {
        "name": result["name"],
        "charger_type": result.get("charger_type", ""),
        "grid_type": result.get("grid_type", ""),
        "run_s": run_s,
        "step_s": step_s,
        "chargers": charger_names,
        "timeline": timeline,
        "markers": markers,
        "score": result["score"],
    }


def build_scenes(scenario_paths: list[str], step_s: float = 5.0) -> list[dict]:
    out = []
    for p in scenario_paths:
        out.append(frames(scenario.run_file(p), step_s=step_s))
    return out


# ---------------------------------------------------------------------------
# Composable grid: target x attack. Two dropdowns in the viewer pick a cell.
# Generated in code (not 38 near-identical YAMLs) so every charger/grid type
# crosses every attack that is meaningful for it. Each tuple is
# (target_key, target_label, attack_key, attack_label, cfg).
# ---------------------------------------------------------------------------
from .targets.charger import CHARGER_SPECS   # noqa: E402
from .targets.microgrid import GRID_SPECS    # noqa: E402

_MON = {"physics_aware": {"divergence_C": 3, "model": {"C": 430_000.0, "R": 0.11}}}


def _charger_combos():
    out = []
    for ct, spec in CHARGER_SPECS.items():
        base = {"ambient_C": 35, "dt_s": 1.0, "monitor": _MON,
                "target": {"type": ct, "limits": {"normal_A": spec.normal_A, "max_A": spec.max_A}},
                "hub": {"grid_type": "single_feeder", "chargers": 1,
                        "transformer_kVA": 500, "impedance_pu": 0.05}}
        oc = dict(id="A-OC", entry_point="cyber.backend_link", mechanism="command_override",
                  field="charging_profile.limit_A", to=spec.max_A, start_s=60)
        spoof = dict(id="A-SPOOF", entry_point="cyber.sensor_bus", mechanism="sensor_spoof",
                     field="sensor.pack_temp_C", hold_value=30, start_s=60)
        out.append((ct, spec.kind, "overcurrent", "Overcurrent — force limit to max",
                    {**base, "run_s": 2400, "name": f"{spec.kind} — overcurrent", "attacks": [oc]}))
        out.append((ct, spec.kind, "overcurrent_tempspoof", "Overcurrent + temp spoof (blinds BMS)",
                    {**base, "run_s": 2400, "name": f"{spec.kind} — overcurrent + temp spoof",
                     "attacks": [oc, spoof]}))
        out.append((ct, spec.kind, "cooling_suppression", "Cooling suppression (temp read low)",
                    {**base, "run_s": 5400, "name": f"{spec.kind} — cooling suppression",
                     "attacks": [spoof]}))
        if spec.bidirectional:
            out.append((ct, spec.kind, "forced_export", "Vehicle-link forced into export",
                        {**base, "run_s": 1800, "name": f"{spec.kind} — forced export",
                         "attacks": [dict(id="A-EXP", entry_point="cyber.vehicle_link",
                                          mechanism="command_override", field="vehicle.requested_A",
                                          to=-spec.max_A, start_s=60)]}))
    return out


def _grid_combos():
    out = []
    for gt, gspec in GRID_SPECS.items():
        def base(n, kVA=690, **hub):
            return {"ambient_C": 35, "dt_s": 1.0, "monitor": _MON,
                    "target": {"type": "charger_dcfast", "limits": {"normal_A": 125, "max_A": 250}},
                    "hub": {"grid_type": gt, "chargers": n, "transformer_kVA": kVA,
                            "impedance_pu": 0.05, **hub}}
        mass = dict(id="A-MASS", entry_point="cyber.hub_controller", mechanism="mass_command",
                    field="charging_profile.limit_A", to=250, start_s=30)
        tk = f"grid_{gt}"
        out.append((tk, gspec.kind, "mass_maxpower", "Mass max-power command → overload",
                    {**base(12), "run_s": 600, "name": f"{gspec.kind} — mass max-power", "attacks": [mass]}))
        out.append((tk, gspec.kind, "loadshed_suppression", "Load-shed dropped → overload pinned",
                    {**base(12), "run_s": 600, "name": f"{gspec.kind} — load-shed suppression",
                     "attacks": [mass, dict(id="A-SHED", entry_point="cyber.hub_controller",
                                            mechanism="dos_blackhole", field="hub.load_shed", start_s=0)]}))
        out.append((tk, gspec.kind, "loadshed_desync", "Load-shed signal arrives 90 s late",
                    {**base(12), "run_s": 600, "name": f"{gspec.kind} — load-shed desync",
                     "attacks": [mass, dict(id="A-DES", entry_point="cyber.hub_controller",
                                            mechanism="desync", field="hub.load_shed", delay_s=90, start_s=0)]}))
        if not gspec.grid_tied:   # islanded / BESS carry frequency + regulated voltage
            out.append((tk, gspec.kind, "freq_push", "Inverter frequency setpoint pushed to 51.5 Hz",
                        {**base(6, kVA=800, inertia_H=3.5), "run_s": 300,
                         "name": f"{gspec.kind} — frequency push",
                         "attacks": [dict(id="A-FREQ", entry_point="cyber.inverter_link",
                                          mechanism="command_override", field="inverter.freq_setpoint_Hz",
                                          to=51.5, start_s=30)]}))
            out.append((tk, gspec.kind, "overvoltage_drift", "Inverter voltage setpoint drifts up",
                        {**base(4, kVA=800), "run_s": 600, "name": f"{gspec.kind} — overvoltage drift",
                         "attacks": [dict(id="A-VD", entry_point="cyber.inverter_link",
                                          mechanism="setpoint_drift", field="inverter.v_setpoint_pu",
                                          rate_per_s=0.0002, start_s=30)]}))
    return out


def build_grid(step_s: float = 5.0) -> list[dict]:
    scenes = []
    for tkey, tlabel, akey, alabel, cfg in _charger_combos() + _grid_combos():
        sc = frames(scenario.run(cfg), step_s=step_s)
        sc.update(target=tkey, target_label=tlabel, attack=akey, attack_label=alabel)
        scenes.append(sc)
    return scenes


if __name__ == "__main__":
    scenes = build_grid()
    Path("viz3d").mkdir(exist_ok=True)
    with open("viz3d/scenes.json", "w", encoding="utf-8") as f:
        json.dump(scenes, f)
    print(f"wrote viz3d/scenes.json ({len(scenes)} scenes: "
          f"{len(set(s['target'] for s in scenes))} targets x attacks)")
