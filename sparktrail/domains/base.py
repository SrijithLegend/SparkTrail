"""Multi-domain base interfaces (SPARKTRAIL_MULTIDOMAIN §2, §4).

A Domain is an infrastructure process: a set of nodes + links, a few consequence
metrics, and a handful of abstract manipulation scenarios. Each domain's
`simulate(scenario, defended)` steps a first-order model and returns a uniform
variant dict the viewer replays — identical shape across all domains.

Scope line (§0): an "attack" is only an out-of-range value on a modelled link at
time T. No exploit, no protocol, no device command. Physics-of-consequence only.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


# §4 manipulation taxonomy — abstract categories mapped to MITRE ATT&CK for ICS.
# (label, mitre, one-line consequence pattern, the defense that catches it)
CATEGORIES = {
    "setpoint_out_of_range": ("Push a setpoint out of range", "T0836 Modify Parameter",
                              "a control value is driven past its safe band", "Physics proxy (hard-limit check)"),
    "spoof_sensor":          ("Freeze / fake a sensor", "T0856 Spoof Reporting Message",
                              "a reading is pinned to a safe-looking value while the process drifts", "Sensor-fusion cross-check"),
    "mass_command":          ("Broadcast a mass command", "T0831 Manipulation of Control",
                              "many devices driven at once past an aggregate limit", "Proxy aggregate-limit check"),
    "suppress_protection":   ("Suppress a protection signal", "T0878 Alarm Suppression",
                              "a safety / alarm / shed signal is dropped", "Proxy refuses to drop safety signals"),
    "replay_delay":          ("Replay / delay a command", "T0857 Point & Tag Modification",
                              "a stale value is re-applied or held past validity", "Residual monitor (model vs reported)"),
    "drift_sensor":          ("Drift a sensor reading", "T0856 Spoof Reporting Message",
                              "a reading slides away from reality too slowly for any one frame to look wrong", "Sensor-fusion cross-check"),
    "replay_reading":        ("Replay a stale reading", "T0857 Replay / T0856 Spoof Reporting",
                              "the last good reading is replayed while the real process keeps moving", "Sensor-fusion cross-check"),
    "synthesize_sensor":     ("Synthesize false sensor data", "T0856 Spoof Reporting (model-aware)",
                              "a fabricated curve with real dynamics hides an absolute offset", "Physics-aware monitor (model vs reported)"),
}


@dataclass
class Node:
    id: str
    label: str
    kind: str                 # attacker | controller | device | process | monitor
    pos: list                 # [x, y, z]


@dataclass
class Metric:
    key: str
    label: str
    unit: str
    limit: float              # the red line
    normal: float             # baseline
    worse: str = "high"       # "high": breach when value > limit; "low": when value < limit


@dataclass
class Scenario:
    id: str
    title: str                # plain-English, consequence-framed
    description: str          # one line: what physically happens
    category: str             # key into CATEGORIES
    mitre_ics: str
    incident_ref: str         # public incident this mirrors (name + year)
    injection: dict           # abstract: {link, setpoint, value, at_s, spoof?}
    run_s: float = 300.0
    step_s: float = 5.0


def bfs_depths(links: list, entry: str) -> dict:
    """Hops from the attacked entry node over the link graph (root = 0)."""
    adj: dict[str, list] = {}
    for a, b in links:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    depths = {entry: 0}
    q = deque([entry])
    while q:
        n = q.popleft()
        for m in adj.get(n, []):
            if m not in depths:
                depths[m] = depths[n] + 1
                q.append(m)
    return depths


def breached(m: Metric, v: float) -> bool:
    return v > m.limit if m.worse == "high" else v < m.limit


class Domain:
    """Subclasses set id/title/nodes/links/metrics and implement `series()`."""
    id: str = ""
    title: str = ""
    nodes: list = []
    links: list = []
    metrics: list = []
    scene_models: dict = {}           # optional node_id -> "models/<id>/x.glb"

    def scenarios(self) -> list:      # list[Scenario]
        raise NotImplementedError

    # --- physics: return per-step metric dict for this scenario -------------
    def series(self, sc: Scenario, defended: bool) -> tuple:
        """Return (frames, markers, proxy_blocked, fusion_caught).
        frames = [{"t": t, "metrics": {key: value}}]; markers = [{t,type,node,label}].
        Implemented per domain."""
        raise NotImplementedError

    # --- shared assembly ----------------------------------------------------
    def entry_node(self, sc: Scenario) -> str:
        link = sc.injection.get("link", "")
        return link.split("->")[-1] if "->" in link else (link or self.nodes[0].id)

    def variant(self, sc: Scenario, defended: bool) -> dict:
        frames, markers, proxy_blocked, fusion_caught = self.series(sc, defended)
        depths = bfs_depths(self.links, self.entry_node(sc))
        peaks, variance_at = {}, None
        for m in self.metrics:
            vals = [fr["metrics"].get(m.key, m.normal) for fr in frames]
            peaks[m.key] = round(max(vals) if m.worse == "high" else min(vals), 2)
            if variance_at is None and not proxy_blocked:
                for fr in frames:
                    if breached(m, fr["metrics"].get(m.key, m.normal)):
                        variance_at = fr["t"]; break
        return {
            "timeline": frames, "depths": depths, "markers": markers,
            "peaks": peaks,
            "flags": {"proxy_blocked": proxy_blocked, "fusion_caught": fusion_caught,
                      "variance_at": variance_at},
        }

    def scene(self) -> dict:
        scs = []
        for sc in self.scenarios():
            cat = CATEGORIES.get(sc.category, (sc.category, sc.mitre_ics, "", ""))
            scs.append({
                "id": sc.id, "title": sc.title, "description": sc.description,
                "category": sc.category, "category_label": cat[0],
                "mitre_ics": sc.mitre_ics, "incident_ref": sc.incident_ref,
                "consequence": cat[2], "defense": cat[3],
                "run_s": sc.run_s, "step_s": sc.step_s,
                "variants": {"undefended": self.variant(sc, False),
                             "defended": self.variant(sc, True)},
            })
        return {
            "id": self.id, "title": self.title,
            "nodes": [n.__dict__ for n in self.nodes],
            "links": self.links,
            "metrics": [m.__dict__ for m in self.metrics],
            "models": self.scene_models,
            "scenarios": scs,
        }
