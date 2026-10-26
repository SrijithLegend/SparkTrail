"""Domain registry + scene generator (SPARKTRAIL_MULTIDOMAIN §2, §10).

    python -m sparktrail.domains      # writes viz3d/scenes/<domain>.json + index.json
"""
from __future__ import annotations

import json
from pathlib import Path

from .ev_hub import EVHub
from .power_sub import PowerSub
from .water import Water
from .robot_cell import RobotCell
from .hvac import HVAC
from .pipeline import Pipeline

REGISTRY = {d.id: d for d in (EVHub(), PowerSub(), Water(), RobotCell(), HVAC(), Pipeline())}


# §10 — non-playable, cited case-study gallery (reporting, not simulation).
CASE_STUDIES = [
    {"domain": "Industrial safety systems", "incident": "Stuxnet (2010)",
     "consequence": "Spoofed 'normal' readings while centrifuges were driven to physical failure.",
     "note": "The archetype for sensor-spoof + overdrive.", "human_harm": False},
    {"domain": "Power grid", "incident": "Ukraine (2015/2016)",
     "consequence": "Remote breaker operation left ~230k people without power.", "human_harm": False},
    {"domain": "Water", "incident": "Oldsmar, FL (2021)",
     "consequence": "Dosing setpoint pushed out of safe range; caught manually.", "human_harm": False},
    {"domain": "Fuel logistics", "incident": "Colonial Pipeline (2021)",
     "consequence": "IT ransomware → precautionary physical shutdown → regional fuel shortage.", "human_harm": False},
    {"domain": "Automotive", "incident": "Jeep remote-control research (2015)",
     "consequence": "Networked entry reached drive-critical systems.",
     "note": "Human-harm domain: cited, not simulated.", "human_harm": True},
    {"domain": "Maritime / aviation", "incident": "GPS/GNSS spoofing",
     "consequence": "Navigation led off course.",
     "note": "Human-harm domain: cited, not simulated.", "human_harm": True},
    {"domain": "Medical devices", "incident": "Connected insulin pumps / pacemakers",
     "consequence": "Research disclosures and FDA recalls over remote-command risk.",
     "note": "Human-harm domain: cited, not simulated.", "human_harm": True},
]


def build(out_dir: str = "viz3d/scenes") -> list:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    index = []
    for did, dom in REGISTRY.items():
        scene = dom.scene()
        (out / f"{did}.json").write_text(json.dumps(scene), encoding="utf-8")
        index.append({"id": did, "title": dom.title,
                      "scenarios": len(scene["scenarios"]), "metrics": len(scene["metrics"])})
    (out / "index.json").write_text(json.dumps(
        {"domains": index, "case_studies": CASE_STUDIES}), encoding="utf-8")
    return index


if __name__ == "__main__":
    idx = build()
    print("wrote viz3d/scenes/: " + ", ".join(f"{d['id']}({d['scenarios']})" for d in idx))
