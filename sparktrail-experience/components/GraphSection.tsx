"use client";
import { useRef } from "react";
import Link from "next/link";
import SparkTrailGraph from "./SparkTrailGraph";
import { useProgress, windowed } from "./useProgress";

export default function GraphSection() {
  const wrap = useRef<HTMLDivElement>(null);
  const p = useProgress(wrap);

  const reveal = windowed(p, 0.0, 0.06, 0.30, 0.38);
  const attack = windowed(p, 0.40, 0.48, 0.70, 0.78);
  const defense = windowed(p, 0.86, 0.92, 1.0, 1.0);

  return (
    <div className="pin-wrap" ref={wrap} id="attack" style={{ height: "480vh" }}>
      <div className="graph-pin">
        <SparkTrailGraph progress={p} />

        <div className="beat center" style={{ opacity: reveal, transform: `translateY(${(1 - reveal) * 24}px)` }}>
          <div className="kicker">Same parts · new surface</div>
          <h2 className="title">The same hardware. Now the attack surface.</h2>
          <p className="sub strong">SparkTrail traces one forged command from the backend, through the charger
            and the battery controller, to the heat in the cells — every hop on one causal graph.</p>
        </div>

        <div className="beat left" style={{ opacity: attack, transform: `translateY(${(1 - attack) * 24}px)` }} id="attack-beat">
          <div className="kicker alert">Propagation</div>
          <h2 className="title alert">Watch it spread.</h2>
          <div className="metrics">
            <div className="metric"><div className="v hot">55.4°C</div><div className="l">real pack temp</div></div>
            <div className="metric"><div className="v warn">30°C</div><div className="l">what the sensor reported</div></div>
            <div className="metric"><div className="v">250A</div><div className="l">forced charge limit</div></div>
          </div>
          <p className="sub">The sensor is pinned to a safe-looking 30 °C while the pack really climbs to 55.4 °C.
            Nothing on the dashboard says so — but the physics does.</p>
        </div>

        <div className="beat center" id="defense" style={{ opacity: defense, transform: `translateY(${(1 - defense) * 24}px)` }}>
          <div className="kicker">Defense</div>
          <h2 className="title">Catch it in the physics,<br />not the paperwork.</h2>
          <p className="sub strong">A cross-layer check compares the electrical load against the thermal response
            and flags the spoof in about one second — before the paperwork ever looks wrong.</p>
          <div className="cta-row">
            <Link href="/simulator" className="btn">Launch Simulator</Link>
            <Link href="/specs" className="btn ghost">Read the architecture</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
