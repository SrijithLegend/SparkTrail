"use client";
import { useEffect, useState } from "react";

/** "Scroll" prompt that fades away once the reader has started moving through the timeline. */
export default function ScrollHint() {
  const [gone, setGone] = useState(false);
  useEffect(() => {
    const onScroll = () => setGone(window.scrollY > window.innerHeight * 0.5);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return (
    <div className={`scroll-hint ${gone ? "gone" : ""}`} aria-hidden>
      <span className="ring" /> Scroll to traverse the timeline
    </div>
  );
}
