"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

// Dual-mode nav: TIMELINE = the story on the home page, VARIANTS = the tools.
const TIMELINE = [
  { href: "/#components", id: "components", label: "Components" },
  { href: "/#attack", id: "attack", label: "Attack" },
  { href: "/#defense", id: "defense", label: "Defense" },
  { href: "/#report", id: "report", label: "Report" },
];
const VARIANTS = [
  { href: "/simulator", id: "/simulator", label: "Simulator" },
  { href: "/specs", id: "/specs", label: "Specs" },
  { href: "https://github.com/SrijithLegend/SparkTrail", id: "github", label: "GitHub" },
];
type Mode = "timeline" | "variants";

export default function Navbar() {
  const path = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [mode, setMode] = useState<Mode>(path === "/" ? "timeline" : "variants");
  const [section, setSection] = useState("");
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 40);
      if (path !== "/") return;
      // active = the last section anchor that has reached the middle of the viewport
      let cur = "";
      for (const s of TIMELINE) {
        const el = document.getElementById(s.id);
        if (el && el.getBoundingClientRect().top <= window.innerHeight * 0.5) cur = s.id;
      }
      setSection(cur);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [path]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const isActive = (id: string) => id === section || id === path;
  const links = mode === "timeline" ? TIMELINE : VARIANTS;

  return (
    <>
      <nav className={`nav ${scrolled || path !== "/" ? "scrolled" : ""}`} aria-label="Primary">
        <Link href="/" className="logo" data-cursor="HOME">
          <span className="ring-wrap"><span className="ring" /></span>SparkTrail
        </Link>
        <span className="clearance">LEVEL 7 CLEARANCE</span>
        <div className="modes" role="group" aria-label="Navigation mode">
          {(["timeline", "variants"] as Mode[]).map((m) => (
            <button key={m} aria-pressed={mode === m} onClick={() => setMode(m)} data-cursor={m.toUpperCase()}>
              {m.toUpperCase()}
            </button>
          ))}
        </div>
        <div className="links">
          {links.map((l) => (
            <a key={l.id} href={l.href} className={isActive(l.id) ? "active" : ""}
               aria-current={isActive(l.id) ? (l.id.startsWith("/") ? "page" : "location") : undefined}>{l.label}</a>
          ))}
        </div>
        <Link href="/simulator" className="btn sm cta" data-magnetic data-cursor="LAUNCH">Launch Simulator</Link>
        <button className="burger" aria-label="Open menu" aria-expanded={open} aria-controls="nav-drawer"
                onClick={() => setOpen(true)}><span /></button>
      </nav>

      <div className={`scrim ${open ? "open" : ""}`} onClick={() => setOpen(false)} aria-hidden />
      <div id="nav-drawer" className={`drawer ${open ? "open" : ""}`} role="dialog" aria-modal="true" aria-label="Menu">
        <button className="close" aria-label="Close menu" onClick={() => setOpen(false)}>×</button>
        <span className="grp">TIMELINE</span>
        {TIMELINE.map((l) => <a key={l.id} href={l.href} onClick={() => setOpen(false)}>{l.label}</a>)}
        <span className="grp">VARIANTS</span>
        {VARIANTS.map((l) => <a key={l.id} href={l.href} onClick={() => setOpen(false)}>{l.label}</a>)}
        <span className="clearance mono" style={{ marginTop: "auto", color: "var(--amber)", fontSize: 11, letterSpacing: ".18em" }}>
          LEVEL 7 CLEARANCE
        </span>
      </div>
    </>
  );
}
