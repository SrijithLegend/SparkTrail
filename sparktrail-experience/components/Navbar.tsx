"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return (
    <nav className={`nav ${scrolled ? "scrolled" : ""}`}>
      <Link href="/" className="logo">SparkTrail</Link>
      <div className="links">
        <a href="#components">Components</a>
        <a href="#attack">Attack</a>
        <a href="#defense">Defense</a>
        <Link href="/specs">Specs</Link>
      </div>
      <Link href="/simulator" className="cta">Launch Simulator</Link>
    </nav>
  );
}
