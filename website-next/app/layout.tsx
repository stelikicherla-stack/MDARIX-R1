import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = { title: "MDARIX | Product lifecycle intelligence", description: "Turn post-market signals into defensible product decisions." };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
