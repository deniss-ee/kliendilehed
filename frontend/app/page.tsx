"use client";

import React, { useEffect, useState } from "react";
import { Search, Sparkles, Tag, RefreshCw, X, RotateCcw } from "lucide-react";
import { api, ProductItem } from "@/lib/api";
import { ProductCard } from "@/components/ProductCard";
import { useFilters } from "@/context/FilterContext";
import { CATEGORIES } from "@/lib/categories";
import { STORES } from "@/lib/stores";

export default function Home() {
  const {
    searchQuery,
    setSearchQuery,
    selectedStores,
    toggleStore,
    selectedCategories,
    toggleCategory,
    onSaleOnly,
    setOnSaleOnly,
    resetAllFilters,
    hasActiveFilters,
    getKeywordsQuery,
  } = useFilters();

  const [products, setProducts] = useState<ProductItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const activeKeywords = getKeywordsQuery();
      const storesParam = selectedStores.length > 0 ? selectedStores.join(",") : undefined;

      const res = await api.searchProducts({
        query: activeKeywords || undefined,
        store: storesParam,
        on_sale_only: onSaleOnly,
      });
      setProducts(res.items);
      setTotalCount(res.total);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timeout = setTimeout(() => {
      fetchProducts();
    }, 150);
    return () => clearTimeout(timeout);
  }, [searchQuery, selectedStores, selectedCategories, onSaleOnly]);

  return (
    <div className="space-y-6">
      {/* Hero Banner */}
      <div className="relative rounded-3xl bg-linear-to-r from-emerald-900 via-slate-900 to-emerald-950 p-6 sm:p-10 text-white shadow-xl overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-bold mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Estonian Supermarket Deal Tracker</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-black tracking-tight leading-tight">
            Compare prices. <span className="text-emerald-400">Save on groceries.</span>
          </h1>
          <p className="mt-2 text-slate-300 text-xs sm:text-sm leading-relaxed">
            Side-by-side tracking across Selver, Rimi, Prisma, Coop & Maxima with normalized metrics & loyalty discounts.
          </p>
        </div>
      </div>

      {/* Main Search Bar & Quick Filters */}
      <div className="bg-white p-4 sm:p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3">
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="w-5 h-5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search product title, brand, or barcode (e.g. Tere piim, Alma või, Paulig)..."
              className="w-full pl-11 pr-4 py-3 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-slate-50/50"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-700"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* On Sale Filter Toggle */}
          <button
            onClick={() => setOnSaleOnly(!onSaleOnly)}
            className={`px-4 py-3 rounded-xl font-bold text-xs flex items-center justify-center gap-2 transition-all cursor-pointer border ${
              onSaleOnly
                ? "bg-red-50 border-red-200 text-red-700 shadow-xs"
                : "bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100"
            }`}
          >
            <Tag className={`w-4 h-4 ${onSaleOnly ? "text-red-600" : "text-slate-400"}`} />
            <span>Deals Only</span>
          </button>
        </div>

        {/* Active Filter Chips Bar */}
        {hasActiveFilters && (
          <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-100">
            <span className="text-2xs font-bold text-slate-400 uppercase tracking-wider mr-1">
              Active Filters:
            </span>

            {/* Selected Stores */}
            {selectedStores.map((st) => (
              <span
                key={st}
                className="inline-flex items-center gap-1 bg-slate-900 text-white text-2xs font-bold px-2.5 py-1 rounded-lg"
              >
                <span>{st}</span>
                <button onClick={() => toggleStore(st)} className="hover:text-red-300">
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}

            {/* Selected Categories */}
            {selectedCategories.map((catId) => {
              const cat = CATEGORIES.find((c) => c.id === catId);
              return (
                <span
                  key={catId}
                  className="inline-flex items-center gap-1 bg-emerald-100 text-emerald-800 text-2xs font-bold px-2.5 py-1 rounded-lg border border-emerald-200"
                >
                  <span>{cat?.icon}</span>
                  <span>{cat?.name_et}</span>
                  <button onClick={() => toggleCategory(catId)} className="hover:text-red-700">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              );
            })}

            {/* Clear All */}
            <button
              onClick={resetAllFilters}
              className="text-2xs font-bold text-red-600 hover:text-red-700 ml-auto flex items-center gap-1 cursor-pointer"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          </div>
        )}
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-black text-slate-900 flex items-center gap-2">
          <span>Products</span>
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-200 text-slate-700">
            {totalCount}
          </span>
        </h2>
      </div>

      {/* Product Grid */}
      {loading ? (
        <div className="py-20 text-center flex flex-col items-center justify-center space-y-3">
          <RefreshCw className="w-8 h-8 text-emerald-600 animate-spin" />
          <p className="text-sm font-semibold text-slate-500">Updating results...</p>
        </div>
      ) : products.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-3">
          <p className="text-slate-700 font-bold">No products match your current filters.</p>
          <p className="text-xs text-slate-400">
            Try unchecking some stores or categories in the left menu.
          </p>
          <button
            onClick={resetAllFilters}
            className="mt-2 inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-900 text-white font-bold text-xs"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Clear Filters</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {products.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      )}
    </div>
  );
}
