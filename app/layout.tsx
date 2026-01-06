import "./globals.css";
import type { Metadata } from "next";
import { Fraunces, Space_Grotesk } from "next/font/google";

const space = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space",
  display: "swap"
});

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap"
});

export const metadata: Metadata = {
  title: "AI Sub Scalp",
  description: "Strict AI promo tracker for free trials, credits, and open-source apps."
};

export default function RootLayout({
  children
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${space.variable} ${fraunces.variable} text-slate-100`}>
        {children}
      </body>
    </html>
  );
}
