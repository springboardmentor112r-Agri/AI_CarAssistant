import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "AutoNegotiator AI — Car Lease & Loan Contract Review",
  description:
    "AI-powered platform to review, analyze, and negotiate your car lease or loan contract. Extract key SLA terms, detect red flags, and get expert negotiation advice.",
  keywords: "car lease, loan contract, AI review, negotiation, APR, VIN lookup, automotive",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <Navbar />
        {children}
      </body>
    </html>
  );
}
