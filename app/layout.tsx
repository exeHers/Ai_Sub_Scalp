import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Deals Hunter",
  description: "Auto-scrapes the web for AI free trials and promo codes."
};

export default function RootLayout({
  children
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}