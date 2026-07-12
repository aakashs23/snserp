import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import { ThemeProvider } from "@/components/theme-provider";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
  display: "swap",
});

const playfair = Playfair_Display({
  variable: "--font-heading",
  subsets: ["latin"],
  display: "swap",
});

// Nonce-based CSP (see utils/supabase/middleware.ts) requires per-request
// rendering so Next can stamp the request's nonce onto its inline scripts.
// This is an internal, fully auth-gated app, so losing static optimization is fine.
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Sri Naga Sai ERP",
  description:
    "AI-Powered ERP & Intelligent Document Management System for Solar Companies. Smart Business Management Powered by AI.",
  keywords: [
    "ERP",
    "Solar",
    "Document Management",
    "AI",
    "Invoice Generator",
    "Sri Naga Sai Energy",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${playfair.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col">
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem
          disableTransitionOnChange
        >
          <TooltipProvider>
            {children}
          </TooltipProvider>
          <Toaster richColors position="top-right" />
        </ThemeProvider>
      </body>
    </html>
  );
}
