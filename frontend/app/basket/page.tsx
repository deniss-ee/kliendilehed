"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  ShoppingBasket,
  Trash2,
  Plus,
  Minus,
  ArrowRight,
  Sparkles,
  CreditCard,
  CheckCircle2,
  TrendingDown,
  Store,
  Split,
  RefreshCw,
} from "lucide-react";
import { useBasket, DEFAULT_LOYALTY_CARDS } from "@/lib/store";
import { api, BasketOptimizationResponse } from "@/lib/api";
import { StoreBadge } from "@/components/StoreBadge";

const formatPrice = (val: any): string => {
  const num = typeof val === "number" ? val : parseFloat(val || "0");
  return isNaN(num) ? "0.00" : num.toFixed(2);
};

export default function BasketPage() {
  const {
    basket,
    loyaltyCards,
    updateQuantity,
    removeItem,
    clearBasket,
    toggleLoyaltyCard,
    totalItemCount,
  } = useBasket();

  const [optimization, setOptimization] = useState<BasketOptimizationResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const runOptimizer = async () => {
    if (basket.length === 0) return;
    setLoading(true);
    try {
      const itemsPayload = basket.map((item) => ({
        canonical_product_id: item.product.id,
        quantity: item.quantity,
      }));
      const res = await api.optimizeBasket(itemsPayload, loyaltyCards);
      setOptimization(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (basket.length > 0) {
      runOptimizer();
    } else {
      setOptimization(null);
    }
  }, [basket, loyaltyCards]);

  if (basket.length === 0) {
    return (
      <div className="max-w-2xl mx-auto text-center py-20 bg-white rounded-3xl border border-slate-200 p-8 shadow-xs">
        <div className="w-16 h-16 bg-emerald-100 text-emerald-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <ShoppingBasket className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-black text-slate-900">Your Basket is Empty</h2>
        <p className="mt-2 text-sm text-slate-500 max-w-sm mx-auto">
          Add items from the store comparison grid to see which Estonian supermarket offers the lowest total cost!
        </p>
        <Link
          href="/"
          className="mt-6 inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm shadow-md shadow-emerald-500/20 transition-all"
        >
          <span>Browse Products & Deals</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-slate-900 flex items-center gap-2">
            <ShoppingBasket className="w-8 h-8 text-emerald-600" />
            <span>Smart Grocery Basket Optimizer</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Analyzing prices across Estonian chains with loyalty cards and split shopping routes.
          </p>
        </div>
        <button
          onClick={clearBasket}
          className="text-xs font-bold text-red-600 hover:text-red-700 flex items-center gap-1 self-start sm:self-auto cursor-pointer"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Clear Basket</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Basket Items & Loyalty Card Options (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Basket Item List */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="p-4 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
              <span className="font-bold text-xs text-slate-700 uppercase tracking-wider">
                Shopping List ({totalItemCount} items)
              </span>
            </div>

            <div className="divide-y divide-slate-100 max-h-96 overflow-y-auto">
              {basket.map((item) => (
                <div key={item.product.id} className="p-4 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-12 h-12 rounded-xl bg-slate-50 border border-slate-100 p-1 flex-shrink-0 flex items-center justify-center">
                      {item.product.image_url ? (
                        <img
                          src={item.product.image_url}
                          alt={item.product.name}
                          className="w-full h-full object-contain mix-blend-multiply"
                        />
                      ) : (
                        <span className="text-3xs text-slate-400">No img</span>
                      )}
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-bold text-slate-900 truncate">{item.product.name}</p>
                      <p className="text-2xs text-slate-500">{item.product.unit}</p>
                    </div>
                  </div>

                  {/* Quantity Controls */}
                  <div className="flex items-center gap-2">
                    <div className="flex items-center border border-slate-200 rounded-lg bg-slate-50">
                      <button
                        onClick={() => updateQuantity(item.product.id, item.quantity - 1)}
                        className="p-1 text-slate-500 hover:text-slate-900 cursor-pointer"
                      >
                        <Minus className="w-3 h-3" />
                      </button>
                      <span className="px-2 text-xs font-bold text-slate-900">{item.quantity}</span>
                      <button
                        onClick={() => updateQuantity(item.product.id, item.quantity + 1)}
                        className="p-1 text-slate-500 hover:text-slate-900 cursor-pointer"
                      >
                        <Plus className="w-3 h-3" />
                      </button>
                    </div>
                    <button
                      onClick={() => removeItem(item.product.id)}
                      className="p-1.5 text-slate-400 hover:text-red-600 rounded-lg"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Loyalty Cards Selection */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-3">
            <div className="flex items-center gap-2">
              <CreditCard className="w-4 h-4 text-emerald-600" />
              <span className="font-bold text-xs text-slate-900 uppercase tracking-wider">
                My Loyalty Cards (Discounts Applied)
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Select the loyalty programs you have to include cardholder discount prices:
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              {DEFAULT_LOYALTY_CARDS.map((card) => {
                const active = loyaltyCards.includes(card);
                return (
                  <button
                    key={card}
                    onClick={() => toggleLoyaltyCard(card)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors cursor-pointer flex items-center gap-1.5 border ${
                      active
                        ? "bg-emerald-50 border-emerald-300 text-emerald-800 shadow-2xs"
                        : "bg-slate-50 border-slate-200 text-slate-400"
                    }`}
                  >
                    {active && <CheckCircle2 className="w-3 h-3 text-emerald-600" />}
                    <span>{card}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column: Optimization Results (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {loading ? (
            <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center flex flex-col items-center justify-center space-y-3">
              <RefreshCw className="w-8 h-8 text-emerald-600 animate-spin" />
              <p className="text-sm font-bold text-slate-700">Calculating cheapest shopping route...</p>
            </div>
          ) : optimization ? (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Best Single Store */}
                <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-2xs font-bold text-slate-500 uppercase tracking-wider">
                        Cheapest Single Store
                      </span>
                      <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-2xs font-bold">
                        1 Stop Trip
                      </span>
                    </div>
                    {optimization.cheapest_single_store ? (
                      <div>
                        <h3 className="text-xl font-black text-slate-900">
                          {optimization.cheapest_single_store.store_name}
                        </h3>
                        <p className="text-3xl font-black text-slate-900 mt-2">
                          {formatPrice(optimization.cheapest_single_store.total_cost)} €
                        </p>
                        {Number(optimization.cheapest_single_store.total_savings) > 0 && (
                          <p className="text-xs font-bold text-emerald-600 mt-1 flex items-center gap-1">
                            <TrendingDown className="w-3.5 h-3.5" />
                            <span>Saves {formatPrice(optimization.cheapest_single_store.total_savings)} € vs regular</span>
                          </p>
                        )}
                      </div>
                    ) : (
                      <p className="text-sm text-slate-400">No single store carries all items.</p>
                    )}
                  </div>
                </div>

                {/* Optimal Split Route */}
                <div className="bg-linear-to-br from-slate-900 to-emerald-950 text-white rounded-2xl p-5 shadow-md flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-2xs font-bold text-emerald-400 uppercase tracking-wider">
                        Smart Split-Store Route
                      </span>
                      <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-2xs font-bold">
                        Maximum Savings
                      </span>
                    </div>
                    <h3 className="text-xl font-black">Multi-Store Strategy</h3>
                    <p className="text-3xl font-black text-emerald-400 mt-2">
                      {formatPrice(optimization.optimized_split_route?.total_cost)} €
                    </p>
                    {Number(optimization.optimized_split_route?.savings_vs_best_single) > 0 && (
                      <p className="text-xs font-bold text-emerald-300 mt-1 flex items-center gap-1">
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>
                          Extra {formatPrice(optimization.optimized_split_route?.savings_vs_best_single)} € saved by splitting
                        </span>
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {/* Where to Buy Breakdown */}
              {optimization.optimized_split_route?.store_breakdown && (
                <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
                  <div className="flex items-center gap-2">
                    <Split className="w-4 h-4 text-emerald-600" />
                    <h3 className="font-bold text-sm text-slate-900 uppercase tracking-wider">
                      Optimized Shopping Breakdown
                    </h3>
                  </div>

                  <div className="space-y-4">
                    {Object.entries(optimization.optimized_split_route.store_breakdown).map(
                      ([storeCode, items]) => (
                        <div key={storeCode} className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-2">
                          <div className="flex items-center justify-between">
                            <StoreBadge storeCode={storeCode} />
                            <span className="text-xs font-bold text-slate-600">
                              {formatPrice(items.reduce((sum, it) => sum + (Number(it.total_price) || 0), 0))} €
                            </span>
                          </div>
                          <div className="divide-y divide-slate-200/60 pt-1">
                            {items.map((it) => (
                              <div key={it.canonical_id} className="py-1.5 flex items-center justify-between text-xs">
                                <span className="text-slate-700 font-medium truncate max-w-xs">
                                  {it.quantity > 1 ? `${it.quantity}x ` : ""}
                                  {it.name}
                                </span>
                                <span className="font-bold text-slate-900">{formatPrice(it.total_price)} €</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )
                    )}
                  </div>
                </div>
              )}

              {/* Single Store Full Rankings */}
              {optimization.single_store_rankings && (
                <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-3">
                  <h3 className="font-bold text-sm text-slate-900 uppercase tracking-wider">
                    All Supermarket Rankings
                  </h3>
                  <div className="divide-y divide-slate-100">
                    {optimization.single_store_rankings.map((store, idx) => (
                      <div key={store.store_code} className="py-3 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-xs font-black text-slate-400 w-4">{idx + 1}</span>
                          <div>
                            <p className="font-bold text-sm text-slate-900">{store.store_name}</p>
                            <p className="text-2xs text-slate-400">
                              {store.missing_items_count > 0
                                ? `Missing ${store.missing_items_count} items`
                                : "All items in stock"}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-black text-base text-slate-900">{formatPrice(store.total_cost)} €</p>
                          {Number(store.total_savings) > 0 && (
                            <p className="text-2xs font-bold text-emerald-600">
                              -{formatPrice(store.total_savings)} € discount
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}

