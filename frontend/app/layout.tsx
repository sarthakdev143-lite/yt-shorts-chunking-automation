import type { Metadata } from "next";
import { IBM_Plex_Mono, Space_Grotesk } from "next/font/google";

import { Providers } from "@/components/providers";
import "./globals.css";

const headingFont = Space_Grotesk({
  variable: "--font-heading",
  subsets: ["latin"],
});

const monoFont = IBM_Plex_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Shortsmith | Video Chunker & Shorts Uploader",
  description:
    "Production-oriented workflow for chunking long-form owned footage into reviewable, scheduler-ready YouTube Shorts.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html className={`${headingFont.variable} ${monoFont.variable} h-full`} lang="en">
      <body className="min-h-full bg-[color:var(--background)] text-[color:var(--foreground)] antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
