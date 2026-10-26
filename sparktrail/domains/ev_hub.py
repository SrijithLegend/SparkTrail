"""EV charging hub domain (§3.1) — wraps the existing engine (§2).

Reuses core.scenario.run (real lumped-thermal + feeder physics, proxy, fusion)
and viz.frames, then maps the result onto the uniform domain variant shape.
"""
from __future__ import annotations

from .base import Domain, Node, Metric, Scenario
from ..core import scenario as _scn
from ..viz import frames as _frames


class EVHub(Domain):
    id = "ev_hub"
    title = "EV charging hub"
    nodes = [
        Node("ATTACKER", "ATTACKER", "attacker", [-9, 0, 0]),
        Node("CSMS", "CSMS", "controller", [-5, 0, 0]),
        Node("CP_1", "CHARGER CP_1", "device", [0, 0, 2]),
        Node("BMS", "BMS", "controller", [3, 0, 2]),
        Node("PACK", "PACK", "process", [7, 0, 2]),
        Node("TRANSFORMER", "TRANSFORMER", "process", [0, 0, -2]),
        Node("FUSION", "FUSION", "monitor", [3, 0, -4]),
    ]
    links = [["ATTACKER", "CSMS"], ["CSMS", "CP_1"], ["CP_1", "BMS"], ["BMS", "PACK"],
             ["CSMS", "TRANSFORMER"], ["CP_1", "FUSION"]]
    metrics = [
        Metric("pack_temp_C", "Pack temperature", "°C", 50.0, 35.0, "high"),
        Metric("transformer_load_pct", "Transformer load", "%", 100.0, 20.0, "high"),
        Metric("bus_voltage_pct", "Bus voltage", "%", 94.0, 100.0, "low"),
    ]
    _CFG = {
        "overcurrent_tempspoof": "scenarios/dcfast_overcurrent_tempspoof.yaml",
        "mass_maxpower": "scenarios/hub_mass_command.yaml",
    }

    def scenarios(self):
        return [
            Scenario("overcurrent_tempspoof", "Overcurrent with the temperature sensor frozen",
                     "The current limit is pushed up while the pack-temp reading is pinned low, so the BMS never derates — the pack overheats.",
                     "spoof_sensor", "T0856 Spoof Reporting Message", "OCPP / charger-security research, 2021–2023",
                     {"link": "ATTACKER->CSMS", "setpoint": "pack_temp_C", "value": 250, "at_s": 60,
                      "spoof": {"reading": 30}}, run_s=2400, step_s=60),
            Scenario("mass_maxpower", "Mass max-power command to every charger",
                     "All chargers are commanded to maximum at once; the shared transformer overloads.",
                     "mass_command", "T0831 Manipulation of Control", "OCPP / charger-security research, 2021–2023",
                     {"link": "ATTACKER->CSMS", "setpoint": "transformer_load_pct", "value": 250, "at_s": 30},
                     run_s=600, step_s=15),
        ]

    def series(self, sc: Scenario, defended: bool):
        cfg = _scn.load(self._CFG[sc.id])
        if defended:
            cfg["proxy"] = True
        result = _scn.run(cfg)
        fr = _frames(result, step_s=sc.step_s)
        first = fr["chargers"][0] if fr["chargers"] else None
        frames = []
        for e in fr["timeline"]:
            temp = e["chargers"].get(first, {}).get("temp", 35.0) if first else 35.0
            frames.append({"t": e["t"], "metrics": {
                "pack_temp_C": round(temp, 1),
                "transformer_load_pct": round(e["load"], 1),
                "bus_voltage_pct": round(e["volt"], 1)}})
        sc_score = result["score"]
        return (frames, fr["markers"], bool(sc_score["proxy_blocked"]),
                sc_score["fusion_alert_t_s"] is not None)
