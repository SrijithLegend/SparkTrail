"use client";
import { RefObject, useEffect, useState } from "react";

/** Progress 0..1 through a tall pin-wrap while its sticky child is pinned. */
export function useProgress(ref: RefObject<HTMLElement>) {
  const [p, setP] = useState(0);
  useEffect(() => {
    let raf = 0;
    const measure = () => {
      raf = 0;
      const el = ref.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const vh = window.innerHeight;
      const total = rect.height - vh; // scrollable distance while pinned
      const scrolled = -rect.top;
      const prog = total > 0 ? scrolled / total : 0;
      setP(Math.min(1, Math.max(0, prog)));
    };
    const onScroll = () => { if (!raf) raf = requestAnimationFrame(measure); };
    measure();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (raf) cancelAnimationFrame(raf);
    };
  }, [ref]);
  return p;
}

/** Linear ramp: 0 before `a`, 1 after `b`, linear between. */
export function ramp(p: number, a: number, b: number) {
  if (p <= a) return 0;
  if (p >= b) return 1;
  return (p - a) / (b - a);
}

/** Visibility window: fades in over [a,b], holds, fades out over [c,d]. */
export function windowed(p: number, a: number, b: number, c: number, d: number) {
  if (p < a || p > d) return 0;
  if (p < b) return (p - a) / (b - a);
  if (p > c) return 1 - (p - c) / (d - c);
  return 1;
}
