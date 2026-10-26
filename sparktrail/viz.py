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


if __name__ == "__main__":
    import sys
    import glob
    # headline first, then the rest sorted for a stable order
    head = "scenarios/dcfast_overcurrent_tempspoof.yaml"
    paths = sys.argv[1:] or [head] + sorted(p.replace("\\", "/") for p in glob.glob("scenarios/*.yaml")
                                            if p.replace("\\", "/") != head)
    scenes = build_scenes(paths)
    Path("viz3d").mkdir(exist_ok=True)
    with open("viz3d/scenes.json", "w", encoding="utf-8") as f:
        json.dump(scenes, f)
    print(f"wrote viz3d/scenes.json ({len(scenes)} scenes)")
