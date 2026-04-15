import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'SILIQUESTA - Advanced CMOS Design Platform',
  description: 'Real physics CMOS simulation with AI co-pilot. 50x faster than traditional EDA.',
  icons: {
    icon: [
      {
        url: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect fill="%2306B6D4" width="100" height="100"/><text x="50" y="75" font-size="80" font-weight="bold" fill="white" text-anchor="middle">S</text></svg>',
        type: 'image/svg+xml',
      },
    ],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="bg-slate-900 text-white">{children}</body>
    </html>
  );
}
