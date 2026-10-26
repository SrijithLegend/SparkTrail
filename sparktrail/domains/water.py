"""Water treatment domain (§3.3). Dosing setpoint + tank level, first-order.

Incident anchors: Oldsmar, FL (2021) — dosing setpoint pushed out of safe band,
caught by an operator.
"""
from __future__ import annotations

from .base import Domain, Node, Metric, Scenario


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


class Water(Domain):
    id = "water"
    title = "Water treatment"
    nodes = [
        Node("ATTACKER", "ATTACKER", "attacker", [-9, 0, 0]),
        Node("HMI", "HMI", "controller", [-5, 0, 0]),
        Node("PLC", "PLC", "controller", [-1, 0, 0]),
        Node("DOSING_PUMP", "DOSING PUMP", "device", [3, 0, 2]),
        Node("VALVE", "INLET VALVE", "device", [3, 0, -2]),
        Node("TANK", "TANK", "process", [7, 0, 0]),
        Node("OUTFLOW", "OUTFLOW", "process", [11, 0, 0]),
        Node("MONITOR", "FUSION", "monitor", [-1, 0, -4]),
    ]
    links = [["ATTACKER", "HMI"], ["HMI", "PLC"], ["PLC", "DOSING_PUMP"],
             ["PLC", "VALVE"], ["DOSING_PUMP", "TANK"], ["VALVE", "TANK"],
             ["TANK", "OUTFLOW"], ["PLC", "MONITOR"]]
    metrics = [
        Metric("dose_ppm", "Dosing concentration", "ppm", 1000.0, 700.0, "high"),
        Metric("tank_level_pct", "Tank level", "%", 100.0, 60.0, "high"),
    ]

    def scenarios(self):
        return [
            Scenario("dosing_oob", "Dosing setpoint pushed out of safe band",
                     "Coagulant dose is driven far past the safe band; treated water goes off-spec.",
                     "setpoint_out_of_range", "T0836 Modify Parameter", "Oldsmar water treatment, 2021",
                     {"link": "PLC->DOSING_PUMP", "setpoint": "dose_ppm", "value": 11000, "at_s": 60},
                     run_s=360, step_s=5),
            Scenario("level_spoof", "Tank level sensor frozen low",
                     "The level reading is pinned low so the inlet valve stays open and the tank overfills.",
                     "spoof_sensor", "T0856 Spoof Reporting Message", "Oldsmar water treatment, 2021",
                     {"link": "TANK->PLC", "setpoint": "tank_level_pct", "value": 60,
                      "at_s": 60, "spoof": {"reading": 40}},
                     run_s=360, step_s=5),
        ]

    def series(self, sc: Scenario, defended: bool):
        inj = sc.injection
        at = inj["at_s"]
        markers = [{"t": at, "type": "attack", "node": self.entry_node(sc),
                    "label": sc.category}]
        proxy_blocked = fusion_caught = False
        frames = []
        dose = 700.0
        level = 60.0
        t = 0.0
        while t <= sc.run_s:
            active = t >= at
            if sc.id == "dosing_oob":
                target = inj["value"] if active else 700.0
                if defended and active and target > 1000.0:
                    target = 1000.0
                    if not proxy_blocked:
                        proxy_blocked = True
                        markers.append({"t": at, "type": "defence", "node": "PLC",
                                        "label": "proxy clamped dose to safe band"})
                dose += (target - dose) * 0.06 * sc.step_s
            else:  # level_spoof
                spoof = inj.get("spoof", {}).get("reading")
                reported = spoof if (active and not (defended and fusion_caught)) else level
                if defended and active and not fusion_caught:
                    fusion_caught = True
                    markers.append({"t": at, "type": "defence", "node": "MONITOR",
                                    "label": "fusion: level reading inconsistent with inflow"})
                    reported = level
                q_in = 3.0 + 0.25 * (60.0 - reported)   # controller opens valve to "raise" level
                q_out = 3.0
                level = _clamp(level + (q_in - q_out) * 0.9 * (sc.step_s / 5.0), 0.0, 130.0)
            frames.append({"t": round(t, 1),
                           "metrics": {"dose_ppm": round(dose, 0), "tank_level_pct": round(level, 1)}})
            t += sc.step_s
        return frames, markers, proxy_blocked, fusion_caught
