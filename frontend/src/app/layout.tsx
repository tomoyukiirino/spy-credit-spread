import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SPY Credit Spread Dashboard",
  description: "Bull Put Credit Spread Auto-Trading System",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
