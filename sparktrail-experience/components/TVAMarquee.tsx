"use client";
import { useEffect, useState } from "react";

/** Infinite ticker. Pauses on hover (CSS); flips direction while the reader scrolls back up. */
export default function TVAMarquee({
  items, speed = 30, reverse = false, accent,
}: { items: string[]; speed?: number; reverse?: boolean; accent?: string }) {
  const [up, setUp] = useState(false);
  useEffect(() => {
    let y = window.scrollY;
    const onScroll = () => { const ny = window.scrollY; if (ny !== y) setUp(ny < y); y = ny; };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const run = (hidden: boolean) => (
    <div className="run" aria-hidden={hidden || undefined}>
      {items.map((t, i) => <span className="item" key={i}>{t}<i>✦</i></span>)}
    </div>
  );
  const style = { "--marquee-speed": `${speed}s`, ...(accent ? { "--marquee-accent": accent } : {}) } as React.CSSProperties;

  return (
    <div className={`marquee ${reverse !== up ? "rev" : ""}`} style={style} role="marquee" aria-label={items.join(" · ")}>
      {/* two identical runs: translating the track by -50% loops seamlessly */}
      <div className="track">{run(false)}{run(true)}</div>
    </div>
  );
}
