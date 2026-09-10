import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MicroLawyer AI",
  description: "Informational legal assistance for Pakistan.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
