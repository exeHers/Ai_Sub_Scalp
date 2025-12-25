import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'AI Deals Hunter',
  description: 'Find free trials, promo codes, and AI discounts automatically.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="dark">
        {children}
      </body>
    </html>
  );
}
