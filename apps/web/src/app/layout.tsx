import type { Metadata } from "next";
import type { ReactNode } from "react";

import { Providers } from "@/components/providers";
import { SiteHeader } from "@/components/site-header";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "WingSaver",
    template: "%s · WingSaver",
  },
  description: "Find and compare airline flights",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <div className="shell">
            <SiteHeader />
            {children}
          </div>
        </Providers>
      </body>
    </html>
  );
}
