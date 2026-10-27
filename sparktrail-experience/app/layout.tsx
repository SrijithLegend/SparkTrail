import type { Metadata, Viewport } from "next";
import "./globals.css";
import { display, mono } from "./fonts";
import TemporalCursor from "@/components/TemporalCursor";

export const metadata: Metadata = {
  title: "SparkTrail — Temporal Variance Detection for the Grid",
  description:
    "A forged command is a variant on the sacred timeline. SparkTrail traces it from packet to heat in EV charging and microgrids — and prunes it in the physics.",
};
export const viewport: Viewport = { themeColor: "#0A0A0F" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${mono.variable}`}>
      <body>
        {children}
        <div className="crt-film" aria-hidden />
        <TemporalCursor />
      </body>
    </html>
  );
}
