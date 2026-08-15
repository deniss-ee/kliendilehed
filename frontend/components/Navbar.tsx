"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShoppingBasket, Sparkles, Store, ShieldCheck } from "lucide-react";
import { useBasket } from "@/lib/store";

export function Navbar() {
  const pathname = usePathname();
  const { totalItemCount } = useBasket();

  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2 group">
          <div className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-between p-2 text-white shadow-md shadow-emerald-500/20 group-hover:scale-105 transition-transform">
            <ShoppingBasket className="w-6 h-6" />
          </div>
          <div>
            <span className="font-extrabold text-lg text-slate-900 tracking-tight flex items-center gap-1.5">
              Soodus<span className="text-emerald-600">Korv</span>
              <span className="text-2xs font-semibold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800">EE</span>
            </span>
            <p className="text-2xs text-slate-500 font-medium">Estonian Grocery Price Tracker</p>
          </div>
        </Link>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 sm:gap-2">
          <Link
            href="/"
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-semibold transition-colors ${
              pathname === "/"
                ? "bg-emerald-50 text-emerald-700"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            <Sparkles className="w-4 h-4 text-emerald-600" />
            <span className="hidden sm:inline">Deals & Search</span>
          </Link>

          <Link
            href="/basket"
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-semibold transition-colors relative ${
              pathname === "/basket"
                ? "bg-emerald-50 text-emerald-700"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            <ShoppingBasket className="w-4 h-4 text-emerald-600" />
            <span>Basket Optimizer</span>
            {totalItemCount > 0 && (
              <span className="ml-1 bg-emerald-600 text-white text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center animate-pulse">
                {totalItemCount}
              </span>
            )}
          </Link>

          <Link
            href="/admin"
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-semibold transition-colors ${
              pathname === "/admin"
                ? "bg-slate-900 text-white"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            <ShieldCheck className="w-4 h-4 text-blue-500" />
            <span className="hidden sm:inline">Admin Curation</span>
          </Link>
        </nav>
      </div>
    </header>
  );
}
