import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Predictive Maintenance Platform",
  description: "Industrial machine failure prediction dashboard — AI4I 2020 dataset",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-zinc-950 text-white min-h-screen">
        <nav className="border-b border-zinc-800 px-6 py-4">
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            <div>
              <span className="text-xs font-black uppercase tracking-widest text-blue-400">
                Predictive Maintenance
              </span>
              <p className="text-[10px] text-zinc-500">AI4I 2020 · XGBoost · FastAPI · AWS</p>
            </div>
            <div className="flex gap-6 text-xs font-semibold text-zinc-400">
              <a href="/" className="hover:text-white transition-colors">Overview</a>
              <a href="/predictions" className="hover:text-white transition-colors">Predictions</a>
              <a href="/model" className="hover:text-white transition-colors">Model</a>
            </div>
          </div>
        </nav>
        <main className="max-w-6xl mx-auto px-6 py-8">{children}</main>
        <footer className="border-t border-zinc-800 px-6 py-4 text-center">
          <p className="text-xs text-zinc-600">
            Arthur Mlambo · Data Science &amp; Mechatronics Engineering · Berlin
          </p>
        </footer>
      </body>
    </html>
  );
}
