"""EV charging hub domain (§3.1) — wraps the existing engine (§2).

Reuses core.scenario.run (real lumped-thermal + feeder physics, proxy, fusion)
and viz.frames, then maps the result onto the uniform domain variant shape.
"""
from __future__ import annotations

from .base import Domain, Node, Metric, Scenario
from ..core import scenario as _scn
from ..viz import frames as _frames

# The four charging-session attacks: forced current + a sensor-side attack on the DC-fast pack,
# all starting at ATTACK_START_S. Shared with gen_attacks.py (the experience site's attack data).
SESSION_BASE = "scenarios/dcfast_overcurrent_tempspoof.yaml"
ATTACK_START_S = 60
SESSION_ATTACKS = {
    "overcurrent_tempspoof": (250, dict(mechanism="sensor_spoof", hold_value=30)),
    "temp_drift":            (210, dict(mechanism="sensor_drift", rate_per_s=0.01)),
    "sensor_replay":         (220, dict(mechanism="replay")),
    "false_data_synthesis":  (230, dict(mechanism="sensor_offset", offset_C=15)),
}
MASS_CFG = "scenarios/hub_mass_command.yaml"


def session_config(key: str) -> dict:
    amps, sensor = SESSION_ATTACKS[key]
    cfg = _scn.load(SESSION_BASE)
    cfg["attacks"] = [
        dict(id="A-INJ", entry_point="cyber.backend_link", mechanism="command_override",
             field="charging_profile.limit_A", to=amps, start_s=ATTACK_START_S),
        dict(id="A-SENS", entry_point="cyber.sensor_bus", field="sensor.pack_temp_C",
             start_s=ATTACK_START_S, **sensor),
    ]
    return cfg


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

    def scenarios(self):
        return [
            Scenario("overcurrent_tempspoof", "Overcurrent with the temperature sensor frozen",
                     "The current limit is pushed up while the pack-temp reading is pinned low, so the BMS never derates — the pack overheats.",
                     "spoof_sensor", "T0856 Spoof Reporting Message", "OCPP / charger-security research, 2021–2023",
                     {"link": "ATTACKER->CSMS", "setpoint": "pack_temp_C", "value": 250, "at_s": 60,
                      "spoof": {"reading": 30}}, run_s=2400, step_s=60),
            Scenario("temp_drift", "Temperature reading drifts low while current is forced up",
                     "The reported pack temperature slides 0.01 °C lower every second at 210 A — no single reading looks wrong, but the BMS derates too late and the pack overheats.",
                     "drift_sensor", "T0856 Spoof Reporting Message", "OCPP / charger-security research, 2021–2023",
                     {"link": "ATTACKER->CSMS", "setpoint": "pack_temp_C", "value": 210, "at_s": 60,
                      "spoof": {"drift_C_per_s": -0.01}}, run_s=2400, step_s=60),
            Scenario("sensor_replay", "Last good temperature frame replayed",
                     "The last good pack-temperature frame is replayed forever at 220 A, so the gauge freezes while the real pack heats behind it.",
                     "replay_reading", "T0857 Replay / T0856 Spoof Reporting", "OCPP / charger-security research, 2021–2023",
                     {"link": "ATTACKER->CSMS", "setpoint": "pack_temp_C", "value": 220, "at_s": 60,
                      "spoof": {"replay": True}}, run_s=2400, step_s=60),
            Scenario("false_data_synthesis", "Fabricated temperature curve, 15 °C low",
                     "A fake reading rises exactly as Joule heating predicts but sits 15 °C below reality at 230 A; only the absolute physics model sees the offset.",
                     "synthesize_sensor", "T0856 Spoof Reporting (model-aware)", "OCPP / charger-security research, 2021–2023",
                     {"link": "ATTACKER->CSMS", "setpoint": "pack_temp_C", "value": 230, "at_s": 60,
                      "spoof": {"offset_C": -15}}, run_s=2400, step_s=60),
            Scenario("mass_maxpower", "Mass max-power command to every charger",
                     "All chargers are commanded to maximum at once; the shared transformer overloads.",
                     "mass_command", "T0831 Manipulation of Control", "OCPP / charger-security research, 2021–2023",
                     {"link": "ATTACKER->CSMS", "setpoint": "transformer_load_pct", "value": 250, "at_s": 30},
                     run_s=600, step_s=15),
        ]

    def series(self, sc: Scenario, defended: bool):
        cfg = session_config(sc.id) if sc.id in SESSION_ATTACKS else _scn.load(MASS_CFG)
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
