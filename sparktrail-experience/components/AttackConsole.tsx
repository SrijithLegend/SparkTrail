"use client";
import { useEffect, useState } from "react";
import SparkTrailGraph from "./SparkTrailGraph";
import { useAttacks, traceUrl, type TraceEvent } from "./useAttacks";

const fmt = (t: number) => `${String(Math.floor(t / 60)).padStart(2, "0")}:${String(Math.round(t % 60)).padStart(2, "0")}`;

/** Pick one of the five engine-generated EV attacks, watch it propagate, replay, read the log. */
export default function AttackConsole() {
  const attacks = useAttacks();
  const [sel, setSel] = useState(0);
  const [play, setPlay] = useState(0);
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const a = attacks[sel];
  const src = traceUrl(a);

  useEffect(() => {
    if (!a) return;
    fetch(src).then((r) => r.json()).then((d) => setEvents(d.events || [])).catch(() => setEvents([]));
  }, [a, src]);

  return (
    <div className="console">
      <aside className="console-rail glass" aria-label="Attack library">
        <div className="rail-head mono">Attack library · {attacks.length}</div>
        {attacks.map((atk, i) => (
          <button key={atk.id} className={`rail-item ${i === sel ? "on" : ""}`} aria-pressed={i === sel}
                  onClick={() => { setSel(i); setPlay((n) => n + 1); }} data-cursor="ANALYZE">
            <span className="ri-n mono">{String(i + 1).padStart(2, "0")}</span>
            <span className="ri-body">
              <span className="ri-title">{atk.title}</span>
              <span className="ri-mitre mono">{atk.mitre}</span>
            </span>
          </button>
        ))}
      </aside>

      <div className="console-main">
        <div className="console-graph crt">
          <SparkTrailGraph interactive src={src} playKey={play} />
          <button className="btn sm replay" onClick={() => setPlay((n) => n + 1)} data-cursor="REPLAY">▸ Replay propagation</button>
          {events.length > 0 && (
            <div className="evlog glass mono" aria-label="Event log">
              {events.map((e) => (
                <div key={e.id} className={e.layer}>{fmt(e.t)}  {e.source.padEnd(11)} {e.kind}</div>
              ))}
            </div>
          )}
        </div>
        {a && (
          <div className="console-panel glass">
            <div className="metrics">
              {a.metrics.map((m, i) => (
                <div className="metric" key={i}><div className={`v ${m.tone || ""}`}>{m.v}</div><div className="l">{m.l}</div></div>
              ))}
            </div>
            <p className="cp-desc">{a.description}</p>
          </div>
        )}
      </div>
    </div>
  );
}
