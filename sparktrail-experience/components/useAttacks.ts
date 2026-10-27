"use client";
import { useEffect, useState } from "react";

// Shape of public/trace/attacks/index.json, written by the repo's gen_attacks.py from the engine.
export type Metric = { v: string; l: string; tone?: string };
export type Attack = {
  id: string; title: string; description: string; mitre: string; kind: "session" | "hub";
  caught_by?: string | null; caught_at_s?: number | null; physics_monitor_at_s?: number | null;
  defended_peak_temp?: number; defended_loading_pct?: number; metrics: Metric[];
};
export type TraceEvent = { id: number; t: number; layer: string; source: string; kind: string; detail: Record<string, unknown> };

export const traceUrl = (a?: Attack) => (a ? `/trace/attacks/${a.id}.json` : "/trace/trace.json");

export function useAttacks() {
  const [attacks, setAttacks] = useState<Attack[]>([]);
  useEffect(() => {
    fetch("/trace/attacks/index.json").then((r) => r.json()).then((d) => setAttacks(d.attacks || [])).catch(() => {});
  }, []);
  return attacks;
}

/** One line for "how the defense handled it", from the engine's numbers. */
export function defenseLine(a?: Attack) {
  if (!a) return "flags the spoof";
  if (a.kind === "hub") return `the Zero-Trust proxy refuses the broadcast, holding the transformer to ${Math.round(a.defended_loading_pct ?? 0)}%`;
  if (a.caught_at_s == null) return "has to rely on the proxy";
  return `${a.caught_at_s === 0 ? "catches this attack the moment it starts" : `flags this attack ${a.caught_at_s} s after it starts`} (${a.caught_by})`;
}
