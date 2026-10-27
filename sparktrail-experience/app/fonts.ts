import { Outfit, Share_Tech_Mono } from "next/font/google";

// Self-hosted at build time by next/font (no runtime request to Google).
export const display = Outfit({
  subsets: ["latin"], weight: ["400", "500", "600", "700", "800"], variable: "--font-display",
});
export const mono = Share_Tech_Mono({ subsets: ["latin"], weight: "400", variable: "--font-mono" });
