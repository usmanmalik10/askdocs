import type { Metadata } from "next";
import "@fontsource/inter/latin-400.css";
import "@fontsource/inter/latin-600.css";
import "@fontsource/inter/latin-700.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "AskDocs — your documents, clear answers",
  description: "Upload a document. Ask a question. Read the source behind every answer. No account required.",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><a className="skip-link" href="#main">Skip to workspace</a>{children}</body></html>;
}
