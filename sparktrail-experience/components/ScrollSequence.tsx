"use client";
import { useEffect, useRef, useState } from "react";
import { windowed } from "./useProgress";

type Beat = {
  align: "center" | "left" | "right";
  a: number; b: number; c: number; d: number;
  kicker?: string; title: string; titleTag?: "h1" | "h2"; sub?: string;
};
type Seq = { dir: string; count: number; pad?: number; ext?: string };

export default function ScrollSequence({
  sequences, heightVh, beats, heroGlow = false,
}: { sequences: Seq[]; heightVh: number; beats: Beat[]; heroGlow?: boolean }) {
  const wrap = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const imgs = useRef<HTMLImageElement[]>([]);
  const progRef = useRef(0);
  const [prog, setProg] = useState(0);
  const total = sequences.reduce((n, s) => n + s.count, 0);

  useEffect(() => {
    const cv = canvas.current, wr = wrap.current;
    if (!cv || !wr) return;
    let raf = 0;

    const sizeCanvas = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      cv.width = Math.floor(window.innerWidth * dpr);
      cv.height = Math.floor(window.innerHeight * dpr);
    };

    const draw = () => {
      const ctx = cv.getContext("2d");
      if (!ctx) return;
      const idx = Math.min(total - 1, Math.max(0, Math.round(progRef.current * (total - 1))));
      const im = imgs.current[idx];
      ctx.fillStyle = "#050505";
      ctx.fillRect(0, 0, cv.width, cv.height);
      if (im && im.complete && im.naturalWidth) {
        const cw = cv.width, ch = cv.height;
        const ir = im.naturalWidth / im.naturalHeight, cr = cw / ch;
        let w = cw, h = ch;
        if (ir > cr) h = cw / ir; else w = ch * ir;
        ctx.drawImage(im, (cw - w) / 2, (ch - h) / 2, w, h);
      }
    };

    // preload
    const arr: HTMLImageElement[] = [];
    sequences.forEach((s) => {
      for (let i = 0; i < s.count; i++) {
        const im = new Image();
        im.src = `${s.dir}/frame_${String(i).padStart(s.pad ?? 3, "0")}.${s.ext ?? "jpg"}`;
        im.onload = draw;
        arr.push(im);
      }
    });
    imgs.current = arr;

    const update = () => {
      raf = 0;
      const rect = wr.getBoundingClientRect();
      const totalPx = rect.height - window.innerHeight;
      const p = totalPx > 0 ? Math.min(1, Math.max(0, -rect.top / totalPx)) : 0;
      progRef.current = p;
      setProg(p);
      draw();
    };
    const onScroll = () => { if (!raf) raf = requestAnimationFrame(update); };
    const onResize = () => { sizeCanvas(); update(); };

    sizeCanvas();
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onResize);
      if (raf) cancelAnimationFrame(raf);
    };
  }, [sequences, total]);

  return (
    <div className="pin-wrap" ref={wrap} style={{ height: `${heightVh}vh` }}>
      <div className="pin">
        {heroGlow && <div className="hero-glow" />}
        <canvas ref={canvas} className="seq-canvas" />
        {beats.map((bt, i) => {
          const o = windowed(prog, bt.a, bt.b, bt.c, bt.d);
          const Tag = bt.titleTag ?? "h2";
          return (
            <div key={i} className={`beat ${bt.align}`}
                 style={{ opacity: o, transform: `translateY(${(1 - o) * 26}px)` }}>
              {bt.kicker && <div className="kicker">{bt.kicker}</div>}
              {Tag === "h1" ? <h1 className="title">{bt.title}</h1> : <h2 className="title">{bt.title}</h2>}
              {bt.sub && <p className="sub">{bt.sub}</p>}
            </div>
          );
        })}
      </div>
    </div>
  );
}
