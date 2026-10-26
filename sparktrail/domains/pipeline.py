"""Pumping / pipeline station (§3.6), first-order.

Incident anchor: pipeline-sector disruption reporting (public, 2021).
"""
from __future__ import annotations

from .base import Domain, Node, Metric, Scenario


class Pipeline(Domain):
    id = "pipeline"
    title = "Pumping / pipeline station"
    nodes = [
        Node("ATTACKER", "ATTACKER", "attacker", [-9, 0, 0]),
        Node("SCADA", "SCADA", "controller", [-5, 0, 0]),
        Node("PLC", "PLC", "controller", [-1, 0, 0]),
        Node("PUMP", "PUMP", "device", [3, 0, 2]),
        Node("PRV", "RELIEF VALVE", "device", [3, 0, -2]),
        Node("SEGMENT", "PIPE SEGMENT", "process", [8, 0, 0]),
        Node("PRESSURE", "PRESSURE", "monitor", [-1, 0, -4]),
    ]
    links = [["ATTACKER", "SCADA"], ["SCADA", "PLC"], ["PLC", "PUMP"], ["PLC", "PRV"],
             ["PUMP", "SEGMENT"], ["PRV", "SEGMENT"], ["PLC", "PRESSURE"]]
    metrics = [
        Metric("line_pressure_bar", "Line pressure", "bar", 70.0, 45.0, "high"),
        Metric("seconds_over", "Seconds over limit", "s", 1.0, 0.0, "high"),
    ]

    def scenarios(self):
        return [
            Scenario("pump_overspeed", "Pump speed setpoint pushed past the limit",
                     "The pump speed setpoint is driven high; line pressure climbs past the pipe's limit.",
                     "setpoint_out_of_range", "T0836 Modify Parameter", "Pipeline-sector disruption, 2021",
                     {"link": "PLC->PUMP", "setpoint": "line_pressure_bar", "value": 92.0, "at_s": 45},
                     run_s=300, step_s=5),
            Scenario("relief_suppress", "Pressure-relief valve disabled",
                     "The relief-valve command is suppressed so pressure is not bled off as it rises.",
                     "suppress_protection", "T0878 Alarm Suppression", "Pipeline-sector disruption, 2021",
                     {"link": "PLC->PRV", "setpoint": "relief", "value": 0, "at_s": 45},
                     run_s=300, step_s=5),
        ]

    def series(self, sc: Scenario, defended: bool):
        inj = sc.injection
        at = inj["at_s"]
        markers = [{"t": at, "type": "attack", "node": self.entry_node(sc), "label": sc.category}]
        proxy_blocked = False
        p, secs = 45.0, 0.0
        frames = []
        t = 0.0
        while t <= sc.run_s:
            active = t >= at
            if sc.id == "pump_overspeed":
                target = inj["value"] if active else 45.0
                if defended and active and target > 70.0:
                    target = 68.0
                    if not proxy_blocked:
                        proxy_blocked = True
                        markers.append({"t": at, "type": "defence", "node": "PLC",
                                        "label": "proxy clamped the pump-speed setpoint"})
                p += (target - p) * 0.2
            else:  # relief_suppress: pressure drifts up, relief cannot bleed it
                relief_ok = not active
                if defended and active:
                    relief_ok = True
                    if not proxy_blocked:
                        proxy_blocked = True
                        markers.append({"t": at, "type": "defence", "node": "PLC",
                                        "label": "proxy refused to disable the relief valve"})
                target = 60.0 if relief_ok else 88.0
                p += (target - p) * 0.15
            if p > 70.0:
                secs += sc.step_s
            frames.append({"t": round(t, 1), "metrics": {
                "line_pressure_bar": round(p, 1), "seconds_over": round(secs, 0)}})
            t += sc.step_s
        return frames, markers, proxy_blocked, False
