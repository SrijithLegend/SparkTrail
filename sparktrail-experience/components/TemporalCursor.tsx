"use client";
import { useEffect, useRef, useState } from "react";

const INTERACTIVE = "a,button,[data-cursor]";

/** Clock-ring cursor: spring-follows the pointer, grows with a context label over links and
 *  buttons, and is pulled toward [data-magnetic] CTAs. Fine pointers only; touch keeps the OS. */
export default function TemporalCursor() {
  const root = useRef<HTMLDivElement>(null);
  const dot = useRef<HTMLDivElement>(null);
  const ring = useRef<HTMLDivElement>(null);
  const [label, setLabel] = useState("");
  const [on, setOn] = useState(false);

  useEffect(() => {
    if (!matchMedia("(pointer: fine)").matches) return;
    setOn(true);
    document.documentElement.classList.add("tc-on");
    const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

    const m = { x: -100, y: -100 }, p = { x: -100, y: -100 }, v = { x: 0, y: 0 };
    let magnet: HTMLElement | null = null, raf = 0;

    const onMove = (e: PointerEvent) => {
      m.x = e.clientX; m.y = e.clientY;
      root.current?.classList.remove("hidden");
      if (dot.current) dot.current.style.transform = `translate(${m.x}px,${m.y}px)`;
    };
    const onOver = (e: MouseEvent) => {
      const el = (e.target as Element).closest?.(INTERACTIVE) as HTMLElement | null;
      root.current?.classList.toggle("hover", !!el);
      magnet = el?.closest("[data-magnetic]") as HTMLElement | null;
      if (el) setLabel(el.dataset.cursor || (el.getAttribute("href")?.includes("simulator") ? "LAUNCH" : "ANALYZE"));
    };
    // leaving the document (or entering an iframe, which has its own cursor): hide the ring
    const onOut = (e: MouseEvent) => { if (!e.relatedTarget) root.current?.classList.add("hidden"); };

    const tick = () => {
      raf = requestAnimationFrame(tick);
      let tx = m.x, ty = m.y;
      if (magnet) { // pull the ring toward the CTA's centre
        const r = magnet.getBoundingClientRect();
        tx += (r.left + r.width / 2 - tx) * 0.45; ty += (r.top + r.height / 2 - ty) * 0.45;
      }
      if (reduce) { p.x = tx; p.y = ty; }
      else { // damped spring
        v.x = (v.x + (tx - p.x) * 0.18) * 0.62; v.y = (v.y + (ty - p.y) * 0.18) * 0.62;
        p.x += v.x; p.y += v.y;
      }
      if (ring.current) ring.current.style.transform = `translate(${p.x}px,${p.y}px)`;
    };

    addEventListener("pointermove", onMove, { passive: true });
    document.addEventListener("mouseover", onOver);
    document.addEventListener("mouseout", onOut);
    raf = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(raf);
      removeEventListener("pointermove", onMove);
      document.removeEventListener("mouseover", onOver);
      document.removeEventListener("mouseout", onOut);
      document.documentElement.classList.remove("tc-on");
    };
  }, []);

  if (!on) return null;
  return (
    <div className="tcur hidden" ref={root} aria-hidden>
      <div className="cring" ref={ring}><span className="lbl">{label}</span></div>
      <div className="dot" ref={dot} />
    </div>
  );
}
