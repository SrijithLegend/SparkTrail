"use client";
import { useEffect, useState } from "react";

/** Opening splash; the CSS animation fades it out, then it unmounts. Skipped for reduced motion. */
export default function Intro() {
  const [gone, setGone] = useState(false);
  useEffect(() => {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) { setGone(true); return; }
    const t = setTimeout(() => setGone(true), 2700);
    return () => clearTimeout(t);
  }, []);
  if (gone) return null;
  return (
    <div className="intro" aria-hidden>
      <span className="ring" style={{ ["--s" as string]: "42px" }} />
      <div className="word">SparkTrail</div>
      <div className="bar" />
      <div className="tag mono">TVA · temporal variance detection</div>
    </div>
  );
}
