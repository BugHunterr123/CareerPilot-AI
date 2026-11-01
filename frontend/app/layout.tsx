import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CareerPilot AI | Placement preparation from your resume",
  description:
    "Upload your resume, see which roles fit, understand each company's hiring stages with sources, and follow a plan built for you.",
};

export const viewport: Viewport = { width: "device-width", initialScale: 1, themeColor: "#F7F6F2" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
