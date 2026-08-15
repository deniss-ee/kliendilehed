"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  ShoppingBasket,
  Sparkles,
  ShieldCheck,
  Tag,
  Check,
  RotateCcw,
  Menu,
  X,
  Store,
  Layers,
} from "lucide-react";
import { useBasket } from "@/lib/store";
import { useFilters } from "@/context/FilterContext";
import { CATEGORIES } from "@/lib/categories";
import { STORES } from "@/lib/stores";

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { totalItemCount } = useBasket();
  const {
    selectedStores,
    toggleStore,
    clearStores,
    selectedCategories,
    toggleCategory,
    clearCategories,
    onSaleOnly,
    toggleOnSaleOnly,
    resetAllFilters,
    hasActiveFilters,
  } = useFilters();

  const [mobileOpen, setMobileOpen] = useState(false);

  const handleStoreClick = (code: string) => {
    if (pathname !== "/") {
      router.push("/");
    }
    toggleStore(code);
  };

  const handleCategoryClick = (catId: string) => {
    if (pathname !== "/") {
      router.push("/");
    }
    toggleCategory(catId);
  };

  const navContent = (
    <div className="flex flex-col h-full space-y-6">
      {/* Brand Header */}
      <Link
        href="/"
        onClick={() => setMobileOpen(false)}
        className="flex items-center gap-3 px-2 py-1 group"
      >
        <div className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-center text-white shadow-md shadow-emerald-500/20 group-hover:scale-105 transition-transform flex-shrink-0">
          <ShoppingBasket className="w-6 h-6" />
        </div>
        <div>
          <span className="font-extrabold text-lg text-slate-900 tracking-tight flex items-center gap-1.5">
            Soodus<span className="text-emerald-600">Korv</span>
            <span className="text-2xs font-semibold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800">EE</span>
          </span>
          <p className="text-3xs text-slate-500 font-medium">Estonian Grocery Price Tracker</p>
        </div>
      </Link>

      {/* Main Pages */}
      <div className="space-y-1">
        <span className="text-3xs font-bold text-slate-400 uppercase tracking-wider px-3 block mb-1">
          Views
        </span>
        <Link
          href="/"
          onClick={() => setMobileOpen(false)}
          className={`flex items-center justify-between px-3 py-2 rounded-xl text-xs font-bold transition-colors ${
            pathname === "/"
              ? "bg-emerald-50 text-emerald-700 font-extrabold shadow-2xs"
              : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
          }`}
        >
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-4 h-4 text-emerald-600" />
            <span>All Deals & Search</span>
          </div>
        </Link>

        <Link
          href="/basket"
          onClick={() => setMobileOpen(false)}
          className={`flex items-center justify-between px-3 py-2 rounded-xl text-xs font-bold transition-colors ${
            pathname === "/basket"
              ? "bg-emerald-50 text-emerald-700 font-extrabold shadow-2xs"
              : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
          }`}
        >
          <div className="flex items-center gap-2.5">
            <ShoppingBasket className="w-4 h-4 text-emerald-600" />
            <span>Basket Optimizer</span>
          </div>
          {totalItemCount > 0 && (
            <span className="bg-emerald-600 text-white text-3xs font-bold px-2 py-0.5 rounded-full animate-pulse">
              {totalItemCount}
            </span>
          )}
        </Link>

        <Link
          href="/admin"
          onClick={() => setMobileOpen(false)}
          className={`flex items-center justify-between px-3 py-2 rounded-xl text-xs font-bold transition-colors ${
            pathname === "/admin"
              ? "bg-slate-900 text-white"
              : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
          }`}
        >
          <div className="flex items-center gap-2.5">
            <ShieldCheck className="w-4 h-4 text-blue-500" />
            <span>Admin Curation</span>
          </div>
        </Link>
      </div>

      {/* Filter Reset Button */}
      {hasActiveFilters && (
        <button
          onClick={resetAllFilters}
          className="flex items-center justify-center gap-1.5 w-full py-2 px-3 rounded-xl bg-slate-100 hover:bg-red-50 hover:text-red-700 text-slate-700 font-bold text-xs transition-colors cursor-pointer border border-slate-200/80"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset All Filters</span>
        </button>
      )}

      {/* Deals Only Toggle */}
      <button
        onClick={toggleOnSaleOnly}
        className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer border ${
          onSaleOnly
            ? "bg-red-50 border-red-200 text-red-700 shadow-2xs"
            : "bg-slate-50 border-slate-200/80 text-slate-700 hover:bg-slate-100"
        }`}
      >
        <div className="flex items-center gap-2">
          <Tag className={`w-3.5 h-3.5 ${onSaleOnly ? "text-red-600" : "text-slate-400"}`} />
          <span>Only On Sale</span>
        </div>
        <span
          className={`w-4 h-4 rounded flex items-center justify-center border ${
            onSaleOnly ? "bg-red-600 border-red-600 text-white" : "border-slate-300 bg-white"
          }`}
        >
          {onSaleOnly && <Check className="w-3 h-3" />}
        </span>
      </button>

      {/* Multi-Store Selection */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between px-3">
          <span className="text-3xs font-bold text-slate-400 uppercase tracking-wider">
            Supermarkets {selectedStores.length > 0 && `(${selectedStores.length})`}
          </span>
          {selectedStores.length > 0 && (
            <button onClick={clearStores} className="text-3xs text-emerald-600 hover:underline font-bold">
              Clear
            </button>
          )}
        </div>
        <div className="space-y-1">
          {Object.values(STORES).map((st) => {
            const isChecked = selectedStores.includes(st.code);
            return (
              <button
                key={st.code}
                onClick={() => handleStoreClick(st.code)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer text-left ${
                  isChecked
                    ? "bg-slate-900 text-white font-bold shadow-2xs"
                    : "text-slate-700 hover:bg-slate-100/80"
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <span
                    className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: st.logoColor }}
                  />
                  <span className="truncate">{st.name}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className={`text-3xs font-mono ${isChecked ? "text-slate-300" : "text-slate-400"}`}>
                    {st.storeCount}
                  </span>
                  <span
                    className={`w-4 h-4 rounded flex items-center justify-center border ${
                      isChecked
                        ? "bg-emerald-500 border-emerald-500 text-white"
                        : "border-slate-300 bg-white"
                    }`}
                  >
                    {isChecked && <Check className="w-3 h-3" />}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Multi-Category Selection */}
      <div className="space-y-1.5 flex-1">
        <div className="flex items-center justify-between px-3">
          <span className="text-3xs font-bold text-slate-400 uppercase tracking-wider">
            Departments {selectedCategories.length > 0 && `(${selectedCategories.length})`}
          </span>
          {selectedCategories.length > 0 && (
            <button onClick={clearCategories} className="text-3xs text-emerald-600 hover:underline font-bold">
              Clear
            </button>
          )}
        </div>
        <div className="space-y-0.5">
          {CATEGORIES.slice(1).map((cat) => {
            const isChecked = selectedCategories.includes(cat.id);
            return (
              <button
                key={cat.id}
                onClick={() => handleCategoryClick(cat.id)}
                className={`w-full flex items-center justify-between px-3 py-1.5 rounded-xl text-xs transition-colors cursor-pointer text-left ${
                  isChecked
                    ? "bg-emerald-50 text-emerald-800 font-bold border border-emerald-200"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80 font-medium"
                }`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-sm">{cat.icon}</span>
                  <span className="truncate">{cat.name_et}</span>
                </div>
                <span
                  className={`w-3.5 h-3.5 rounded flex items-center justify-center border ${
                    isChecked
                      ? "bg-emerald-600 border-emerald-600 text-white"
                      : "border-slate-300 bg-white"
                  }`}
                >
                  {isChecked && <Check className="w-2.5 h-2.5" />}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Footer Info */}
      <div className="pt-4 border-t border-slate-200 text-3xs text-slate-400 px-3 space-y-1">
        <p className="font-bold text-slate-600">SoodusKorv EE</p>
        <p>100% Local Multi-Store Resolution Engine.</p>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile Top Header */}
      <div className="lg:hidden sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-slate-200 px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white">
            <ShoppingBasket className="w-5 h-5" />
          </div>
          <span className="font-extrabold text-base text-slate-900">
            Soodus<span className="text-emerald-600">Korv</span>
          </span>
        </Link>

        <div className="flex items-center gap-2">
          <Link
            href="/basket"
            className="p-2 rounded-xl bg-slate-100 text-slate-700 relative"
          >
            <ShoppingBasket className="w-5 h-5" />
            {totalItemCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-emerald-600 text-white text-3xs font-bold w-4 h-4 rounded-full flex items-center justify-center">
                {totalItemCount}
              </span>
            )}
          </Link>
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="p-2 rounded-xl bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Backdrop */}
      {mobileOpen && (
        <div
          onClick={() => setMobileOpen(false)}
          className="lg:hidden fixed inset-0 z-50 bg-slate-950/40 backdrop-blur-xs"
        />
      )}

      {/* Mobile Drawer Panel */}
      <aside
        className={`lg:hidden fixed top-0 bottom-0 left-0 z-50 w-72 bg-white p-6 shadow-2xl transition-transform duration-200 overflow-y-auto ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex justify-end mb-2">
          <button onClick={() => setMobileOpen(false)} className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100">
            <X className="w-5 h-5" />
          </button>
        </div>
        {navContent}
      </aside>

      {/* Desktop Sticky Left Sidebar */}
      <aside className="hidden lg:block w-64 xl:w-72 bg-white border-r border-slate-200/80 p-6 min-h-screen sticky top-0 h-screen overflow-y-auto flex-shrink-0 shadow-xs">
        {navContent}
      </aside>
    </>
  );
}
