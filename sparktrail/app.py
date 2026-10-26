"""Phase 4 — live "Chaos Engineering" console.

    pip install -r requirements-app.txt
    streamlit run app.py

Left  = Attack Console: pick a YAML scenario, optionally force the Zero-Trust
        proxy ON, and run it through the real sim engine.
Right = Live Defence Log: the resulting trace (attack / control / monitor),
        newest first.
Bottom= manual sensor-spoof tester that runs the Phase-2 fusion validator and
        the Phase-1 proxy live, so you can watch the defence catch a spoof.

Everything is simulation — the same engine the CLI and 3D viewer use.
"""
from __future__ import annotations

import glob
import os

import streamlit as st
import pandas as pd

from sparktrail.core import scenario
from sparktrail.core.events import EventStore
from sparktrail.control.proxy import PhysicsProxy
from sparktrail.monitor.sensor_fusion import SensorFusionValidator

st.set_page_config(page_title="SparkTrail — Chaos Console", layout="wide")
st.markdown("## ⚡ SparkTrail — Cyber-to-Physical Chaos Console")
st.caption("Inject an attack on the left. Watch the physics-aware defence react on the right. "
           "Nothing touches real hardware — every attack is a value injected into a model.")

SCN = sorted(glob.glob("scenarios/*.yaml"))
left, right = st.columns([1, 1.3])

with left:
    st.subheader("Attack Console")
    path = st.selectbox("Scenario", SCN, format_func=lambda p: os.path.basename(p))
    force_proxy = st.toggle("Force Zero-Trust proxy ON (Phase 1)", value=False)
    if st.button("▸ EXECUTE TEMPORAL EVENT", type="primary", use_container_width=True):
        cfg = scenario.load(path)
        if force_proxy:
            cfg["proxy"] = True
        st.session_state["result"] = scenario.run(cfg)

    r = st.session_state.get("result")
    if r:
        sc = r["score"]
        st.markdown(f"**{r['name']}**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Peak pack temp", f'{sc["peak_pack_temp_C"]} °C',
                  "BLOCKED" if sc["proxy_blocked"] else None)
        c2.metric("Transformer load", f'{sc["peak_transformer_load_pct"]} %')
        c3.metric("Impact score", sc["impact_score"])
        c4, c5, c6 = st.columns(3)
        c4.metric("Proxy refusals", sc["proxy_rejects"])
        c5.metric("Fusion caught spoof",
                  "—" if sc["fusion_alert_t_s"] is None else f'{sc["fusion_alert_t_s"]:.0f}s')
        c6.metric("Max propagation depth", sc["max_propagation_depth"])
        if sc["proxy_blocked"]:
            st.success("Phase 1 proxy refused the over-limit command — the plant stayed within limits.")
        if sc["fusion_alert_t_s"] is not None:
            st.info(f"Phase 2 fusion flagged a spoofed sensor at {sc['fusion_alert_t_s']:.0f}s.")

with right:
    st.subheader("Live Defence Log")
    r = st.session_state.get("result")
    if r:
        rows = [{"t_s": e["t"], "layer": e["layer"], "node": e["node"],
                 "kind": e["kind"], "field": e["field"], "value": e["value"],
                 "depth": e["propagation_depth"]}
                for e in r["events"]
                if e["layer"] in ("attack", "control", "monitor")]
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.drop_duplicates(subset=["layer", "node", "kind", "field"], keep="first")
            st.dataframe(df.iloc[::-1], use_container_width=True, height=320)
            st.caption(f'{len(r["events"])} total events · node depths: {r["node_depths"]}')
    else:
        st.info("No trace yet — run a scenario.")

st.divider()
st.subheader("Manual Sensor-Spoof Tester (Phase 1 proxy + Phase 2 fusion, live)")
a, b, c, d = st.columns(4)
current = a.slider("Measured current (A)", 0, 400, 250)
reported_prev = b.slider("Reported temp, previous (°C)", 20, 70, 35)
reported_now = c.slider("Reported temp, now (°C)", 20, 70, 35)
dt = d.slider("Δt (s)", 1, 60, 10)

v = SensorFusionValidator(EventStore(), h=300.0, T_amb=35.0, persist=1, min_load_A=50.0)
v.step(dt, 0.0, current, 400.0, reported_prev)          # seed previous reading
caught = bool(v.step(dt, dt, current, 400.0, reported_now))  # judge this reading
if caught:
    st.error(f"🚨 SENSOR SPOOF DETECTED — reported rise {reported_now - reported_prev:+.1f} °C is "
             f"implausibly low for {current} A over {dt}s (energy balance says it should be higher).")
else:
    st.success("Fusion check PASS — reported thermal response is consistent with the electrical load.")

p = PhysicsProxy(thermal_limit_A=160.0)
st.caption(f"Zero-Trust proxy: {current} A "
           + ("within limits." if current <= p.thermal_limit_A
              else f"would be CLAMPED to {p.thermal_limit_A:.0f} A."))

# ----------------------------------------------------------------- multi-domain
st.divider()
st.subheader("Multi-domain playground (SPARKTRAIL_MULTIDOMAIN)")
from sparktrail.domains import REGISTRY  # noqa: E402
from sparktrail.domains.base import CATEGORIES  # noqa: E402

dcol1, dcol2 = st.columns([1, 2])
dom = dcol1.selectbox("Domain", list(REGISTRY), format_func=lambda k: REGISTRY[k].title)
D = REGISTRY[dom]
scn = dcol2.selectbox("Manipulation", D.scenarios(),
                      format_func=lambda s: f"{s.title}  ·  {s.mitre_ics}")
u = D.variant(scn, defended=False)
d = D.variant(scn, defended=True)
_defense = CATEGORIES.get(scn.category, ("", "", "", "—"))[3]
st.caption(f"Prior occurrence: **{scn.incident_ref}** · defense: {_defense}")
rows = []
for m in D.metrics:
    rows.append({"metric": m.label, "unit": m.unit, "limit": m.limit,
                 "undefended peak": u["peaks"][m.key], "defended peak": d["peaks"][m.key]})
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
uf, df = u["flags"], d["flags"]
if uf["variance_at"] is not None:
    st.error(f"Undefended: VARIANCE at T+{uf['variance_at']:.0f}s.")
if df["proxy_blocked"] or df["fusion_caught"] and df["variance_at"] is None:
    st.success("Defended: proxy/fusion kept the process in band.")
