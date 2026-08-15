"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import {
  Store,
  ExternalLink,
  CreditCard,
  Tag,
  ArrowLeft,
  Search,
  Sparkles,
  RefreshCw,
} from "lucide-react";
import { STORES, StoreProfile } from "@/lib/stores";
import { api, ProductItem } from "@/lib/api";
import { ProductCard } from "@/components/ProductCard";

export default function StoreDetailPage({
  params,
}: {
  params: Promise<{ store: string }>;
}) {
  const unwrappedParams = use(params);
  const slug = (unwrappedParams.store || "selver").toLowerCase();
  const profile: StoreProfile | undefined = STORES[slug];

  const [products, setProducts] = useState<ProductItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [dealsOnly, setDealsOnly] = useState(false);

  useEffect(() => {
    if (!profile) return;
    setLoading(true);
    api
      .searchProducts({
        store: profile.code,
        query: query.trim() || undefined,
        on_sale_only: dealsOnly,
      })
      .then((res) => {
        setProducts(res.items);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [slug, profile, query, dealsOnly]);

  if (!profile) {
    return (
      <div className="text-center py-20 bg-white rounded-3xl border border-slate-200 p-8">
        <h2 className="text-2xl font-bold text-slate-900">Store Not Found</h2>
        <Link href="/" className="mt-4 inline-flex items-center gap-2 text-emerald-600 font-bold">
          <ArrowLeft className="w-4 h-4" /> Back to Deals
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Back Button */}
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-500 hover:text-slate-900 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to All Supermarkets</span>
      </Link>

      {/* Store Banner */}
      <div className={`relative rounded-3xl bg-linear-to-r ${profile.bannerBg} p-8 sm:p-12 text-white shadow-xl overflow-hidden`}>
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/10 backdrop-blur-xs text-white text-xs font-bold mb-3 border border-white/20">
              <Store className="w-3.5 h-3.5" />
              <span>{profile.storeCount} Locations Across Estonia</span>
            </div>
            <h1 className="text-3xl sm:text-5xl font-black tracking-tight">{profile.name}</h1>
            <p className="text-sm sm:text-base text-white/80 font-medium italic mt-1">
              "{profile.slogan}"
            </p>
          </div>

          {/* Quick Links */}
          <div className="flex flex-wrap gap-2">
            <a
              href={profile.flyerUrl}
              target="_blank"
              rel="noreferrer"
              className="px-4 py-2.5 rounded-xl bg-white text-slate-900 font-bold text-xs flex items-center gap-1.5 shadow-md hover:bg-slate-100 transition-colors"
            >
              <Tag className="w-3.5 h-3.5 text-red-600" />
              <span>Official Kliendileht</span>
              <ExternalLink className="w-3 h-3 text-slate-400" />
            </a>
            <a
              href={profile.websiteUrl}
              target="_blank"
              rel="noreferrer"
              className="px-4 py-2.5 rounded-xl bg-white/20 backdrop-blur-xs text-white font-bold text-xs flex items-center gap-1.5 border border-white/30 hover:bg-white/30 transition-colors"
            >
              <span>Visit Online Store</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>

        {/* Loyalty Program Info Box */}
        <div className="mt-6 pt-6 border-t border-white/15 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-white/90">
          <div className="flex items-start gap-2.5 bg-white/10 backdrop-blur-xs p-3.5 rounded-xl border border-white/15">
            <CreditCard className="w-4 h-4 text-amber-300 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block text-white">{profile.loyaltyCardName}</span>
              <span className="text-white/80 text-2xs leading-relaxed">{profile.loyaltyBenefit}</span>
            </div>
          </div>
          <div className="flex items-start gap-2.5 bg-white/10 backdrop-blur-xs p-3.5 rounded-xl border border-white/15">
            <Sparkles className="w-4 h-4 text-emerald-300 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block text-white">Automated Price Resolution</span>
              <span className="text-white/80 text-2xs leading-relaxed">
                Daily scraped prices, regular vs promotional comparisons, and barcode-matched savings.
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Catalog Search Controls */}
      <div className="bg-white p-4 sm:p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`Search ${profile.name} products...`}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-slate-50/50"
          />
        </div>
        <button
          onClick={() => setDealsOnly(!dealsOnly)}
          className={`px-4 py-2.5 rounded-xl font-bold text-xs flex items-center justify-center gap-2 transition-all cursor-pointer border ${
            dealsOnly
              ? "bg-red-50 border-red-200 text-red-700 shadow-xs"
              : "bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100"
          }`}
        >
          <Tag className={`w-3.5 h-3.5 ${dealsOnly ? "text-red-600" : "text-slate-400"}`} />
          <span>{profile.name} Deals Only</span>
        </button>
      </div>

      {/* Product Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-black text-slate-900 flex items-center gap-2">
            <span>Available at {profile.name}</span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-200 text-slate-700">
              {products.length}
            </span>
          </h2>
        </div>

        {loading ? (
          <div className="py-20 text-center flex flex-col items-center justify-center space-y-3">
            <RefreshCw className="w-8 h-8 text-emerald-600 animate-spin" />
            <p className="text-sm font-semibold text-slate-500">Loading {profile.name} catalog...</p>
          </div>
        ) : products.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-2">
            <p className="text-slate-700 font-bold">No products found for this query in {profile.name}.</p>
            <p className="text-xs text-slate-400">Try searching for other keywords.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {products.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
