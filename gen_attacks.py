"""Generate the experience site's five EV attacks from the real engine.

    python gen_attacks.py

Runs each attack (undefended, and again with the Zero-Trust proxy on) through
sparktrail.core.scenario and writes, for the site's attack selector and console:

    sparktrail-experience/public/trace/attacks/<id>.json   graph depths + key-event timeline
    sparktrail-experience/public/trace/attacks/index.json  titles, MITRE tags, metrics, copy

Every number on the site's attack cards comes from these runs; nothing is typed in by hand.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from sparktrail.core import scenario

OUT = Path(__file__).parent / "sparktrail-experience" / "public" / "trace" / "attacks"
SESSION = "scenarios/dcfast_overcurrent_tempspoof.yaml"   # DC-fast charger, one pack
HUB = "scenarios/hub_mass_command.yaml"                   # 12-charger hub on one transformer
PACK_LIMIT_C = 50.0                                        # BMS derate threshold
START = 60                                                 # attack onset in the session runs

# id, title, MITRE ATT&CK for ICS tag, forced current, sensor-side attack, copy (engine numbers are appended)
SESSION_ATTACKS = [
    ("overcurrent", "Forced overcurrent + temperature spoof", "T0836 Modify Parameter + T0856 Spoof Reporting",
     250, dict(mechanism="sensor_spoof", hold_value=30),
     "The charge current is forced to 250 A while the temperature sensor is pinned to a safe-looking 30 °C, "
     "so the BMS never derates and the pack cooks."),
    ("temp_drift", "Thermal-sensor drift", "T0856 Spoof Reporting Message",
     200, dict(mechanism="sensor_drift", rate_per_s=0.01),
     "The reported temperature slides 0.01 °C lower every second — no single reading looks wrong, but the gap "
     "from reality keeps widening while current is pushed up."),
    ("replay", "Sensor replay / stale freeze", "T0857 Replay / T0856 Spoof Reporting",
     220, dict(mechanism="replay"),
     "The last good telemetry frame is replayed forever, so the gauge freezes while real current keeps heating "
     "the pack behind it."),
    ("synthesis", "False-data synthesis", "T0856 Spoof Reporting (model-aware)",
     230, dict(mechanism="sensor_offset", offset_C=15),
     "A fabricated temperature curve that rises exactly as Joule heating predicts, just 15 °C below reality — "
     "built to pass rate checks, so the absolute physics model has to catch it."),
]


def _first(events, pred):
    return next((e for e in events if pred(e)), None)


def _ev(i, t, layer, source, kind, detail):
    return {"id": i, "t": t, "layer": layer, "source": source, "kind": kind, "detail": detail}


def session_attack(aid, title, mitre, amps, sensor, desc):
    cfg = copy.deepcopy(scenario.load(SESSION))
    cfg["name"] = title
    cfg["attacks"] = [
        dict(id="A-INJ", entry_point="cyber.backend_link", mechanism="command_override",
             field="charging_profile.limit_A", to=amps, start_s=START),
        dict(id="A-SENS", entry_point="cyber.sensor_bus", field="sensor.pack_temp_C", start_s=START, **sensor),
    ]
    run = scenario.run(cfg)
    s, ev = run["score"], run["events"]
    defended = copy.deepcopy(cfg); defended["proxy"] = True
    d = scenario.run(defended)["score"]

    # earliest physics-aware detection after onset: sensor fusion or the model monitor
    hits = [(t - START, who) for t, who in [(s["fusion_alert_t_s"], "sensor fusion"),
                                            (s["monitor_alert_t_s"], "physics monitor")] if t is not None]
    caught_s, caught_by = min(hits) if hits else (None, None)
    over = _first(ev, lambda e: e["field"] == "pack_temp_C" and e["value"] >= PACK_LIMIT_C)
    cur = _first(ev, lambda e: e["field"] == "current_A" and e["t"] >= START and e["value"] >= amps * 0.95)

    timeline = [
        _ev(1, START, "attack", "ATTACKER", "attack.inject", {"forced_a": amps, "sensor": sensor["mechanism"]}),
        _ev(2, START, "cyber", "CSMS", "ocpp.SetChargingProfile", {"limit_a": amps}),
        _ev(3, cur["t"] if cur else START, "control", "CP_1", "charger.apply_limit", {"current_a": amps}),
        _ev(4, START, "cyber", "BMS", f"bms.reading_{sensor['mechanism']}", {}),
    ]
    if over:
        timeline.append(_ev(5, over["t"], "physics", "PACK", "pack.over_limit", {"temp_c": PACK_LIMIT_C}))
    if s["fusion_alert_t_s"] is not None:
        timeline.append(_ev(6, s["fusion_alert_t_s"], "monitor", "FUSION", "monitor.sensor_spoof", {}))
    if s["monitor_alert_t_s"] is not None:
        timeline.append(_ev(7, s["monitor_alert_t_s"], "monitor", "MONITOR", "monitor.alarm", {}))
    timeline.sort(key=lambda e: (e["t"], e["id"]))

    peak, dpeak = s["peak_pack_temp_C"], d["peak_pack_temp_C"]
    meta = {
        "id": aid, "title": title, "mitre": mitre, "kind": "session",
        "description": f"{desc} Real peak {peak:.1f} °C; with the proxy on, {dpeak:.1f} °C.",
        "peak_real_temp": round(peak, 1), "defended_peak_temp": round(dpeak, 1), "commanded_a": float(amps),
        "caught_by": caught_by, "caught_at_s": None if caught_s is None else round(caught_s),
        "physics_monitor_at_s": None if s["monitor_alert_t_s"] is None else round(s["monitor_alert_t_s"] - START),
        "metrics": [
            {"v": f"{peak:.1f}°C", "l": "real pack temp", "tone": "hot"},
            {"v": f"{amps}A", "l": "forced current", "tone": ""},
            {"v": "missed" if caught_s is None else "at onset" if round(caught_s) == 0 else f"+{round(caught_s)}s",
             "l": f"flagged by {caught_by}" if caught_by else "not flagged", "tone": "ok"},
        ],
    }
    depths = {"ATTACKER": 0, "CSMS": 1, "CP_1": 2, "BMS": 3, "PACK": 4, "FUSION": 5, "MONITOR": 5}
    return meta, {"meta": meta, "node_depths": depths, "events": timeline}


def mass_attack():
    cfg = scenario.load(HUB)
    run = scenario.run(cfg)
    s, ev = run["score"], run["events"]
    d = scenario.run(scenario.load("scenarios/hub_mass_command_defended.yaml"))["score"]
    start = cfg["attacks"][0]["start_s"]
    n = cfg["hub"]["chargers"]
    over = _first(ev, lambda e: e["field"] == "transformer_load_pct" and e["value"] > 100)
    sag = _first(ev, lambda e: e["field"] == "bus_voltage_pct" and e["value"] < 94)
    load, drop, dload = s["peak_transformer_load_pct"], 100 - s["min_bus_voltage_pct"], d["peak_transformer_load_pct"]

    timeline = [
        _ev(1, start, "attack", "ATTACKER", "attack.inject", {"mechanism": "mass_command"}),
        _ev(2, start, "control", "HUB", "hub.broadcast_max_power", {"chargers": n, "limit_a": 250}),
    ]
    if over:
        timeline.append(_ev(3, over["t"], "physics", "TRANSFORMER", "transformer.overload", {"load_pct": round(load, 1)}))
    if sag:
        timeline.append(_ev(4, sag["t"], "physics", "CP_7", "bus.undervoltage", {"bus_pct": s["min_bus_voltage_pct"]}))
    meta = {
        "id": "mass_command", "title": "Mass max-power broadcast", "mitre": "T0831 Manipulation of Control",
        "kind": "hub",
        "description": (f"One forged command drives all {n} chargers in the hub to full power at once, overloading the "
                        f"shared transformer to {load:.0f}% and sagging the bus {drop:.1f}%. The Zero-Trust proxy "
                        f"refuses it and holds the load to {dload:.0f}%."),
        "loading_pct": round(load, 1), "vdrop_pct": round(drop, 1), "defended_loading_pct": round(dload, 1),
        "caught_by": "Zero-Trust proxy", "caught_at_s": None,
        "metrics": [
            {"v": f"{load:.0f}%", "l": "transformer loading", "tone": "hot"},
            {"v": f"{drop:.1f}%", "l": "bus voltage drop", "tone": "warn"},
            {"v": f"{dload:.0f}%", "l": "with the proxy on", "tone": "ok"},
        ],
    }
    depths = {"ATTACKER": 0, "HUB": 1, "TRANSFORMER": 2, "CP_7": 3}
    return meta, {"meta": meta, "node_depths": depths, "events": timeline}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for spec in SESSION_ATTACKS:
        meta, trace = session_attack(*spec)
        index.append(meta)
        (OUT / f"{meta['id']}.json").write_text(json.dumps(trace, indent=1, ensure_ascii=False), encoding="utf-8")
    meta, trace = mass_attack()
    index.append(meta)
    (OUT / "mass_command.json").write_text(json.dumps(trace, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT / "index.json").write_text(json.dumps({"attacks": index}, indent=1, ensure_ascii=False), encoding="utf-8")
    for m in index:
        print(f"{m['id']:<13} " + " · ".join(f"{x['v']} {x['l']}" for x in m["metrics"]))


if __name__ == "__main__":
    main()
