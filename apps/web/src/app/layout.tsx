import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SecureAI Studio",
  description: "AI へ送る前に、必ず SecureAI を通す — 共通 PII 保護レイヤー",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
