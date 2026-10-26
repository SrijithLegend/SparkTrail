"""Power substation / feeder domain (§3.2), first-order.

Incident anchors: Ukraine grid (2015/2016) — remote breaker operation → blackout.
"""
from __future__ import annotations

from .base import Domain, Node, Metric, Scenario


class PowerSub(Domain):
    id = "power_sub"
    title = "Power substation / feeder"
    nodes = [
        Node("ATTACKER", "ATTACKER", "attacker", [-9, 0, 0]),
        Node("SCADA", "SCADA", "controller", [-5, 0, 0]),
        Node("RTU", "RTU", "controller", [-1, 0, 0]),
        Node("BREAKER", "BREAKER", "device", [3, 0, 2]),
        Node("TAP_CHANGER", "TAP CHANGER", "device", [3, 0, -2]),
        Node("FEEDER", "FEEDER", "process", [7, 0, 0]),
        Node("LOADS", "LOADS", "process", [11, 0, 0]),
        Node("MONITOR", "MONITOR", "monitor", [-1, 0, -4]),
    ]
    links = [["ATTACKER", "SCADA"], ["SCADA", "RTU"], ["RTU", "BREAKER"],
             ["RTU", "TAP_CHANGER"], ["BREAKER", "FEEDER"], ["TAP_CHANGER", "FEEDER"],
             ["FEEDER", "LOADS"], ["RTU", "MONITOR"]]
    metrics = [
        Metric("served_load_MW", "Served load", "MW", 20.0, 40.0, "low"),
        Metric("bus_voltage_pu", "Bus voltage", "pu", 1.06, 1.00, "high"),
        Metric("customers_out", "Customers dropped", "k", 1.0, 0.0, "high"),
    ]

    def scenarios(self):
        return [
            Scenario("breaker_open", "Remote breaker operation sheds the feeder",
                     "Feeder breakers are commanded open; served load collapses and customers go dark.",
                     "suppress_protection", "T0878 Alarm Suppression", "Ukraine grid, 2015",
                     {"link": "RTU->BREAKER", "setpoint": "breaker_open", "value": 1, "at_s": 45},
                     run_s=300, step_s=5),
            Scenario("tap_overvoltage", "Tap-changer setpoint pushed out of range",
                     "The voltage-regulation setpoint is driven high; the bus rises past its limit.",
                     "setpoint_out_of_range", "T0836 Modify Parameter", "Ukraine grid, 2016",
                     {"link": "RTU->TAP_CHANGER", "setpoint": "bus_voltage_pu", "value": 1.14, "at_s": 45},
                     run_s=300, step_s=5),
        ]

    def series(self, sc: Scenario, defended: bool):
        inj = sc.injection
        at = inj["at_s"]
        markers = [{"t": at, "type": "attack", "node": self.entry_node(sc), "label": sc.category}]
        proxy_blocked = False
        served, volt, cust = 40.0, 1.0, 0.0
        frames = []
        t = 0.0
        while t <= sc.run_s:
            active = t >= at
            if sc.id == "breaker_open":
                open_cmd = active
                if defended and active:          # proxy refuses to drop supply
                    open_cmd = False
                    if not proxy_blocked:
                        proxy_blocked = True
                        markers.append({"t": at, "type": "defence", "node": "RTU",
                                        "label": "proxy refused to drop the supply/breaker signal"})
                target_served = 2.0 if open_cmd else 40.0
                served += (target_served - served) * 0.3
                cust = round((40.0 - served) / 40.0 * 230.0, 0)   # ~230k on this feeder
            else:  # tap_overvoltage
                target_v = inj["value"] if active else 1.0
                if defended and active and target_v > 1.06:
                    target_v = 1.05
                    if not proxy_blocked:
                        proxy_blocked = True
                        markers.append({"t": at, "type": "defence", "node": "RTU",
                                        "label": "proxy clamped the tap setpoint"})
                volt += (target_v - volt) * 0.25
            frames.append({"t": round(t, 1), "metrics": {
                "served_load_MW": round(served, 1), "bus_voltage_pu": round(volt, 3),
                "customers_out": round(cust, 0)}})
            t += sc.step_s
        return frames, markers, proxy_blocked, False
