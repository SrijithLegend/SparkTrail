"use client";
import { useRef, useState } from "react";
import Link from "next/link";
import SparkTrailGraph from "./SparkTrailGraph";
import { useProgress, windowed } from "./useProgress";
import { useAttacks, traceUrl, defenseLine } from "./useAttacks";

export default function GraphSection() {
  const wrap = useRef<HTMLDivElement>(null);
  const p = useProgress(wrap);
  const attacks = useAttacks();
  const [sel, setSel] = useState(0);
  const a = attacks[sel];

  const reveal = windowed(p, 0.0, 0.06, 0.30, 0.38);
  const attack = windowed(p, 0.40, 0.48, 0.70, 0.78);
  const defense = windowed(p, 0.86, 0.92, 1.0, 1.0);

  // keep the graph clear of the text: reveal text is on the right, attack text on
  // the left (graph slides the other way; upward on phones); behind the centred
  // CTA it recedes
  const side = attack - reveal;
  const mobile = typeof window !== "undefined" && window.innerWidth < 1100; // matches globals.css
  const graphStyle = {
    // one template for both layouts, so the server render (no window) matches at p=0
    transform: `translate(${mobile ? 0 : side * 21}vw, ${mobile ? -Math.abs(side) * 22 : 0}vh) ` +
      `scale(${mobile ? 1 : 1 - 0.15 * Math.abs(side)})`,
    opacity: 1 - 0.75 * defense,
  };

  return (
    <div className="pin-wrap" ref={wrap} style={{ height: "520vh" }}>
      {/* nav targets at the attack and defense beats: p = at·520/420 */}
      <span id="attack" className="anchor" style={{ top: "44.4%" }} />
      <span id="defense" className="anchor" style={{ top: "76.7%" }} />
      <div className="graph-pin crt">
        <div className="graph-mount" style={graphStyle}>
          <SparkTrailGraph progress={p} src={traceUrl(a)} />
        </div>

        <div className="beat right" style={{ opacity: reveal, transform: `translateY(${(1 - reveal) * 24}px)` }}>
          <span className="tva-stamp">TVA case file 101</span>
          <div className="kicker">Variant detected</div>
          <h2 className="title split">The hardware,<br />now the attack surface.</h2>
          <p className="sub strong">SparkTrail traces one forged command from the backend, through the charger
            and the battery controller, to the heat in the cells — every hop on one causal graph.</p>
        </div>

        <div className="beat left" style={{ opacity: attack, transform: `translateY(${(1 - attack) * 24}px)`,
             pointerEvents: attack > 0.5 ? "auto" : "none" }}>
          <span className="tva-stamp red">Temporal breach</span>
          <div className="kicker alert">Variant propagation{a ? ` · ${a.mitre}` : ""}</div>
          <h2 className="title alert split atk-title">{a ? a.title : "Watch it spread."}</h2>
          {a && (
            <div className="metrics">
              {a.metrics.map((m, i) => (
                <div className="metric" key={i}><div className={`v ${m.tone || ""}`}>{m.v}</div><div className="l">{m.l}</div></div>
              ))}
            </div>
          )}
          {a && <p className="sub atk-desc">{a.description}</p>}
          <div className="atk-chips" role="group" aria-label="Choose an attack">
            {attacks.map((atk, i) => (
              <button key={atk.id} className={`atk-chip ${i === sel ? "on" : ""}`} aria-pressed={i === sel}
                      onClick={() => setSel(i)} data-cursor="SELECT">
                {String(i + 1).padStart(2, "0")} · {atk.title.split(/ [+/] /)[0]}
              </button>
            ))}
          </div>
        </div>

        <div className="beat center" style={{ opacity: defense, transform: `translateY(${(1 - defense) * 24}px)`,
             pointerEvents: defense > 0.5 ? "auto" : "none" }}>
          <span className="tva-stamp green">Timeline pruned</span>
          <div className="kicker safe">Temporal defense</div>
          <h2 className="title safe split">Catch it in the physics,<br />not the paperwork.</h2>
          <p className="sub strong">An independent physics check compares the electrical load against the thermal
            response and {defenseLine(a)} — before the dashboard ever looks wrong.</p>
          <div className="cta-row">
            <Link href="/console" className="btn" data-magnetic data-cursor="LAUNCH">Open the attack console</Link>
            <Link href="/simulator" className="btn ghost" data-magnetic data-cursor="LAUNCH">Launch Simulator</Link>
            <Link href="/specs" className="btn ghost" data-magnetic data-cursor="ANALYZE">Read the architecture</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
