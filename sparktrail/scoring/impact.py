"""Impact score from the event graph. Weighted combo of:
peak deviation, time-to-impact (faster = worse), physical nodes affected,
detection delay. Higher = worse. Lets scenarios be ranked by physical effect.
"""
from __future__ import annotations

from ..core.events import Event


def score(events: list[Event], baselines: dict | None = None,
          thresholds: dict | None = None) -> dict:
    thresholds = thresholds or {"pack_temp_C": 45.0}
    phys = [e for e in events if e.layer == "physics" and isinstance(e.value, (int, float))]

    peak_temp = max((e.value for e in phys if e.field == "pack_temp_C"), default=0.0)
    peak_load = max((e.value for e in phys if e.field == "transformer_load_pct"), default=0.0)
    min_volt = min((e.value for e in phys if e.field == "bus_voltage_pct"), default=100.0)
    max_volt = max((e.value for e in phys if e.field == "bus_voltage_pct"), default=100.0)
    freqs = [e.value for e in phys if e.field == "frequency_Hz"]
    coolant_peak = max((e.value for e in phys if e.field == "coolant_temp_C"), default=None)
    freq_nadir = min(freqs) if freqs else None
    freq_peak = max(freqs) if freqs else None
    rocofs = [e.value for e in phys if e.field == "rocof_Hz_s"]
    peak_rocof = max((abs(v) for v in rocofs), default=None)

    # time to first threshold crossing (temp)
    thr = thresholds.get("pack_temp_C", 45.0)
    crossings = [e.t for e in phys if e.field == "pack_temp_C" and e.value >= thr]
    time_to_impact = min(crossings) if crossings else None

    nodes = {e.node for e in phys}

    alerts = [e for e in events if e.layer == "monitor" and e.kind == "alert"]
    detect_t = alerts[0].t if alerts else None
    detection_delay = (detect_t - time_to_impact) if (detect_t and time_to_impact) else None

    # crude composite (0..100-ish); documented as illustrative weighting
    peak_term = max(0.0, peak_temp - thr) * 1.5
    load_term = max(0.0, peak_load - 100.0) * 0.5
    volt_term = (max(0.0, 100.0 - min_volt) + max(0.0, max_volt - 100.0)) * 0.8
    freq_term = (abs(50.0 - freq_nadir) * 20 if freq_nadir else 0.0) + \
                (abs(freq_peak - 50.0) * 20 if freq_peak else 0.0)
    speed_term = (600.0 / time_to_impact) if time_to_impact else 0.0  # ponytail: hand-tuned weights
    node_term = len(nodes) * 3.0
    total = round(peak_term + load_term + volt_term + freq_term + speed_term + node_term, 1)

    return {
        "impact_score": total,
        "peak_pack_temp_C": round(peak_temp, 2),
        "peak_coolant_temp_C": round(coolant_peak, 2) if coolant_peak is not None else None,
        "peak_transformer_load_pct": round(peak_load, 1),
        "min_bus_voltage_pct": round(min_volt, 1),
        "max_bus_voltage_pct": round(max_volt, 1),
        "freq_nadir_Hz": round(freq_nadir, 3) if freq_nadir is not None else None,
        "freq_peak_Hz": round(freq_peak, 3) if freq_peak is not None else None,
        "peak_rocof_Hz_s": round(peak_rocof, 4) if peak_rocof is not None else None,
        "time_to_impact_s": time_to_impact,
        "physical_nodes_affected": sorted(nodes),
        "detection_delay_s": detection_delay,
        "monitor_alert_t_s": detect_t,
    }
