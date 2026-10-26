"""Manufacturing robot cell (unoccupied) (§3.4), first-order.

Incident anchor: ICS robotics-security research (public academic demonstrations).
Consequence lands on the PART and the cell, never a person.
"""
from __future__ import annotations

from .base import Domain, Node, Metric, Scenario


class RobotCell(Domain):
    id = "robot_cell"
    title = "Manufacturing robot cell"
    nodes = [
        Node("ATTACKER", "ATTACKER", "attacker", [-9, 0, 0]),
        Node("CELL_CTRL", "CELL CTRL", "controller", [-5, 0, 0]),
        Node("PLC", "PLC", "controller", [-1, 0, 0]),
        Node("ROBOT_AXIS", "ROBOT AXIS", "device", [3, 0, 2]),
        Node("CONVEYOR", "CONVEYOR", "device", [3, 0, -2]),
        Node("PART", "PART", "process", [7, 0, 0]),
        Node("SAFETY_ZONE", "SAFETY ZONE", "monitor", [-1, 0, -4]),
    ]
    links = [["ATTACKER", "CELL_CTRL"], ["CELL_CTRL", "PLC"], ["PLC", "ROBOT_AXIS"],
             ["PLC", "CONVEYOR"], ["ROBOT_AXIS", "PART"], ["CONVEYOR", "PART"],
             ["PLC", "SAFETY_ZONE"]]
    metrics = [
        Metric("position_error_mm", "Positional error", "mm", 0.50, 0.02, "high"),
        Metric("parts_scrapped", "Parts out of tolerance", "", 1.0, 0.0, "high"),
    ]

    def scenarios(self):
        return [
            Scenario("axis_offset_drift", "Axis offset nudged out of tolerance",
                     "A small position offset is injected and accumulates until parts fall out of tolerance.",
                     "setpoint_out_of_range", "T0836 Modify Parameter", "ICS robotics-security research",
                     {"link": "PLC->ROBOT_AXIS", "setpoint": "position_error_mm", "value": 0.9, "at_s": 40},
                     run_s=300, step_s=5),
            Scenario("interlock_bypass", "Safety-zone interlock signal suppressed",
                     "The cell interlock signal is dropped so the cell keeps running when it should have stopped.",
                     "suppress_protection", "T0878 Alarm Suppression", "ICS robotics-security research",
                     {"link": "PLC->SAFETY_ZONE", "setpoint": "interlock", "value": 0, "at_s": 40},
                     run_s=300, step_s=5),
        ]

    def series(self, sc: Scenario, defended: bool):
        inj = sc.injection
        at = inj["at_s"]
        markers = [{"t": at, "type": "attack", "node": self.entry_node(sc), "label": sc.category}]
        proxy_blocked = False
        err, scrap = 0.02, 0.0
        frames = []
        t = 0.0
        while t <= sc.run_s:
            active = t >= at
            if sc.id == "axis_offset_drift":
                off = inj["value"] if active else 0.02
                if defended and active and off > 0.5:
                    off = 0.4
                    if not proxy_blocked:
                        proxy_blocked = True
                        markers.append({"t": at, "type": "defence", "node": "PLC",
                                        "label": "proxy clamped the axis offset"})
                err += (off - err) * 0.08
                if err > 0.5:
                    scrap += 0.3
            else:  # interlock_bypass
                dropped = active
                if defended and active:
                    dropped = False
                    if not proxy_blocked:
                        proxy_blocked = True
                        markers.append({"t": at, "type": "defence", "node": "PLC",
                                        "label": "proxy refused to drop the interlock signal"})
                if dropped:
                    err += 0.02
                    scrap += 0.2
            frames.append({"t": round(t, 1), "metrics": {
                "position_error_mm": round(err, 3), "parts_scrapped": round(scrap, 0)}})
            t += sc.step_s
        return frames, markers, proxy_blocked, False
