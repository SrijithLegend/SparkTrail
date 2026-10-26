import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SparkTrail — Cyber-to-Physical Impact Visibility",
  description:
    "See a forged command become real heat. Cyber-to-physical impact visibility for EV charging and microgrids.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
