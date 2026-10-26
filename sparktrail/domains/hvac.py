"""Building HVAC / cold storage (§3.5), first-order.

Incident anchor: building-automation compromise via third-party BMS access
(public breach reporting). Consequence lands on the cold room / stock.
"""
from __future__ import annotations

from .base import Domain, Node, Metric, Scenario


class HVAC(Domain):
    id = "hvac"
    title = "Building HVAC / cold storage"
    nodes = [
        Node("ATTACKER", "ATTACKER", "attacker", [-9, 0, 0]),
        Node("BMS", "BMS", "controller", [-5, 0, 0]),
        Node("CONTROLLER", "CONTROLLER", "controller", [-1, 0, 0]),
        Node("CHILLER", "CHILLER", "device", [3, 0, 2]),
        Node("DAMPER", "DAMPER", "device", [3, 0, -2]),
        Node("COLDROOM", "COLD ROOM", "process", [8, 0, 0]),
        Node("MONITOR", "MONITOR", "monitor", [-1, 0, -4]),
    ]
    links = [["ATTACKER", "BMS"], ["BMS", "CONTROLLER"], ["CONTROLLER", "CHILLER"],
             ["CONTROLLER", "DAMPER"], ["CHILLER", "COLDROOM"], ["DAMPER", "COLDROOM"],
             ["CONTROLLER", "MONITOR"]]
    metrics = [
        Metric("coldroom_temp_C", "Cold-room temperature", "°C", 8.0, 4.0, "high"),
        Metric("minutes_out", "Minutes outside band", "min", 1.0, 0.0, "high"),
    ]

    def scenarios(self):
        return [
            Scenario("setpoint_raise", "Chiller setpoint pushed up",
                     "The cooling setpoint is driven high; the cold room warms past the safe band and stock is at risk.",
                     "setpoint_out_of_range", "T0836 Modify Parameter", "Building-automation compromise (public reporting)",
                     {"link": "CONTROLLER->CHILLER", "setpoint": "coldroom_temp_C", "value": 16.0, "at_s": 60},
                     run_s=600, step_s=10),
            Scenario("temp_spoof", "Cold-room sensor frozen at safe value",
                     "The temperature reading is pinned at 4 °C while cooling is cut, so no alarm fires as the room warms.",
                     "spoof_sensor", "T0856 Spoof Reporting Message", "Building-automation compromise (public reporting)",
                     {"link": "COLDROOM->CONTROLLER", "setpoint": "coldroom_temp_C", "value": 4.0,
                      "at_s": 60, "spoof": {"reading": 4.0}}, run_s=600, step_s=10),
        ]

    def series(self, sc: Scenario, defended: bool):
        inj = sc.injection
        at = inj["at_s"]
        markers = [{"t": at, "type": "attack", "node": self.entry_node(sc), "label": sc.category}]
        proxy_blocked = fusion_caught = False
        temp, mins = 4.0, 0.0
        frames = []
        t = 0.0
        while t <= sc.run_s:
            active = t >= at
            if sc.id == "setpoint_raise":
                target = inj["value"] if active else 4.0
                if defended and active and target > 8.0:
                    target = 7.5
                    if not proxy_blocked:
                        proxy_blocked = True
                        markers.append({"t": at, "type": "defence", "node": "CONTROLLER",
                                        "label": "proxy clamped the chiller setpoint"})
                temp += (target - temp) * 0.05 * (sc.step_s / 10.0)
            else:  # temp_spoof: cooling cut, reading frozen -> room warms unnoticed
                if defended and active and not fusion_caught:
                    fusion_caught = True
                    markers.append({"t": at, "type": "defence", "node": "MONITOR",
                                    "label": "fusion: flat reading inconsistent with cooling state"})
                cooling = (not active) or fusion_caught   # fusion catch restores cooling for the rest
                target = 4.0 if cooling else 18.0
                temp += (target - temp) * 0.04 * (sc.step_s / 10.0)
            if temp > 8.0:
                mins += sc.step_s / 60.0
            frames.append({"t": round(t, 1), "metrics": {
                "coldroom_temp_C": round(temp, 2), "minutes_out": round(mins, 1)}})
            t += sc.step_s
        return frames, markers, proxy_blocked, fusion_caught
