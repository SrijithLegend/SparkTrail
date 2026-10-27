"use client";
import { useEffect, useRef, useState } from "react";

// Every figure comes from the repo's engine (scenarios/*.yaml via sparktrail.core.scenario)
// or the multi-domain sweep; keep them in sync with /specs and the simulator.
type Stat = {
  value: number; decimals?: number; text?: string; unit?: string; label: string; note: string;
  stamp: string; tone?: "hot" | "safe"; size?: "wide" | "tall"; fill?: number;
};
const STATS: Stat[] = [
  { value: 57.7, decimals: 1, unit: "°C", label: "Real pack peak", tone: "hot", size: "wide", fill: 96,
    note: "While the spoofed sensor reports a calm 30 °C. DC-fast overcurrent, 250 A forced.", stamp: "Variant" },
  { value: 174, unit: "%", label: "Transformer load", tone: "hot", fill: 87,
    note: "Mass max-power command across a 12-charger hub.", stamp: "Breach" },
  { value: 8.7, decimals: 1, unit: "%", label: "Bus voltage drop", fill: 72,
    note: "Feeder impedance model at peak load.", stamp: "Breach" },
  { value: 43.2, decimals: 1, unit: "°C", label: "Defended peak", tone: "safe", size: "tall", fill: 40,
    note: "The Zero-Trust proxy refuses the authenticated-but-dangerous 250 A command. Same attack, pruned timeline.",
    stamp: "Pruned" },
  { value: 2, unit: "s", label: "Spoof flagged", tone: "safe",
    note: "Sensor fusion closes the energy balance two seconds after the attack starts.", stamp: "Caught" },
  { value: 15, text: "15/15", label: "Variants pruned", tone: "safe", size: "wide", fill: 100,
    note: "Every manipulation across all 6 domains breaches undefended and is contained with the defense on.",
    stamp: "Pruned" },
  { value: 0, text: "6 × 5", label: "Targets", note: "Six charger types, five microgrid topologies.", stamp: "Classified" },
  { value: 7, label: "Attack mechanisms", size: "wide", // wide: completes the 4-column bento's last row
    note: "Override, spoof, drift, mass command, DoS, replay, desync — across six entry points.", stamp: "Classified" },
];

function Counter({ s, run }: { s: Stat; run: boolean }) {
  const [v, setV] = useState(0);
  useEffect(() => {
    if (!run || s.text) return;
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) { setV(s.value); return; }
    let raf = 0; const t0 = performance.now();
    const step = (t: number) => {
      const k = Math.min(1, (t - t0) / 1300);
      setV(s.value * (1 - Math.pow(1 - k, 3)));
      if (k < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [run, s]);
  return <>{s.text ?? v.toFixed(s.decimals ?? 0)}{s.unit && <small>{s.unit}</small>}</>;
}

export default function TVAStatsGrid() {
  const ref = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current; if (!el) return;
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setInView(true); io.disconnect(); } },
      { threshold: 0.2 });
    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <section className="section tva-grid" id="report">
      <div className="wrap">
        <div className="section-head">
          <h2>Temporal Variance <em>Report</em></h2>
          <p>Measured, not imagined. Every number is the simulator&apos;s own output — run the scenarios and the same
            figures come out.</p>
        </div>
        <div className={`bento ${inView ? "in" : ""}`} ref={ref}>
          {STATS.map((s, i) => (
            <div key={s.label} className={`card glass ${s.tone ?? ""} ${s.size ?? ""}`}
                 style={{ transitionDelay: `${i * 70}ms`, ["--fill" as string]: `${s.fill ?? 0}%` }}>
              <span className={`tva-stamp ${s.tone === "hot" ? "red" : s.tone === "safe" ? "green" : ""}`}>{s.stamp}</span>
              <div>
                <div className="v"><Counter s={s} run={inView} /></div>
                <div className="k">{s.label}</div>
                <p>{s.note}</p>
              </div>
              {s.fill !== undefined && <div className="bar"><i /></div>}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
