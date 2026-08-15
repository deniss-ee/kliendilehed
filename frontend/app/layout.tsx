import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";
import { BasketProvider } from "@/context/BasketContext";
import { FilterProvider } from "@/context/FilterContext";

export const metadata: Metadata = {
  title: "SoodusKorv - Estonian Grocery Price Comparison & Basket Optimizer",
  description:
    "Compare grocery prices across Selver, Rimi, Prisma, Coop, Maxima and Lidl in Estonia. Find the cheapest supermarket and optimize your shopping basket.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="et">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased selection:bg-emerald-500 selection:text-white">
        <BasketProvider>
          <FilterProvider>
            <div className="flex flex-col lg:flex-row min-h-screen">
              {/* Left Sidebar Menu */}
              <Sidebar />

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0">
              <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {children}
              </main>

              <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-400">
                <div className="max-w-7xl mx-auto px-4">
                  <p className="font-semibold text-slate-600">SoodusKorv EE — Estonian Retail Price Tracker</p>
                  <p className="mt-1 text-3xs text-slate-400">
                    100% Local-First Engine • Tracking Selver, Rimi, Prisma, Coop, Maxima, Grossi & Lidl.
                  </p>
                </div>
              </footer>
            </div>
          </div>
        </FilterProvider>
      </BasketProvider>
    </body>
  </html>
);
}
