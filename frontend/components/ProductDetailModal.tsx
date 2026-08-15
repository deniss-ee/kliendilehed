"use client";

import React, { useEffect, useState } from "react";
import {
  X,
  Tag,
  ExternalLink,
  ShoppingBasket,
  Plus,
  Minus,
  Trash2,
  TrendingDown,
  Scale,
  Sparkles,
  RefreshCw,
} from "lucide-react";
import { ProductItem } from "@/lib/api";
import { StoreBadge } from "./StoreBadge";
import { PriceHistoryChart, PricePoint } from "./PriceHistoryChart";
import { useBasket } from "@/lib/store";

interface ProductDetailModalProps {
  product: ProductItem;
  onClose: () => void;
}

const formatPrice = (val: any): string => {
  const num = typeof val === "number" ? val : parseFloat(val || "0");
  return isNaN(num) ? "0.00" : num.toFixed(2);
};

export function ProductDetailModal({ product, onClose }: ProductDetailModalProps) {
  const { addItem, updateQuantity, getItemQuantity } = useBasket();
  const quantity = getItemQuantity(product.id);

  const [history, setHistory] = useState<PricePoint[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  useEffect(() => {
    fetch(`/api/products/${product.id}/history`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setHistory(data))
      .catch(console.error)
      .finally(() => setLoadingHistory(false));
  }, [product.id]);

  const sortedOffers = [...product.offers].sort(
    (a, b) => (Number(a.effective_price) || 0) - (Number(b.effective_price) || 0)
  );
  const bestOffer = sortedOffers[0];

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-3xl max-w-3xl w-full border border-slate-200 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-2">
            <span className="text-2xs font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-md uppercase tracking-wider">
              {product.brand || "Estonian Grocery"}
            </span>
            {product.ean && (
              <span className="text-3xs text-slate-400 font-mono">EAN: {product.ean}</span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
          {/* Top Section: Image + Title + Best Price & Stepper */}
          <div className="flex flex-col sm:flex-row gap-6 items-start">
            <div className="w-full sm:w-48 aspect-square rounded-2xl bg-slate-50 border border-slate-100 p-3 flex items-center justify-center flex-shrink-0 overflow-hidden">
              {product.image_url ? (
                <img
                  src={product.image_url}
                  alt={product.name}
                  className="w-full h-full object-contain mix-blend-multiply"
                />
              ) : (
                <span className="text-xs text-slate-300">No Image</span>
              )}
            </div>

            <div className="flex-1 space-y-3">
              <h2 className="text-xl sm:text-2xl font-black text-slate-900 leading-snug">
                {product.name}
              </h2>

              <div className="flex items-center gap-2">
                <span className="text-xs font-bold px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700">
                  Unit: {product.unit}
                </span>
                {product.has_discount && (
                  <span className="text-xs font-black px-2.5 py-1 rounded-lg bg-red-100 text-red-700 flex items-center gap-1">
                    <Tag className="w-3.5 h-3.5" />
                    <span>ON SALE</span>
                  </span>
                )}
              </div>

              {/* Best Price Callout */}
              <div className="pt-2 flex items-baseline gap-3">
                <span className="text-3xl font-black text-slate-900">
                  {bestOffer ? `${formatPrice(bestOffer.effective_price)} €` : "-"}
                </span>
                {bestOffer && (
                  <span className="text-xs font-bold text-emerald-700">
                    Cheapest at {bestOffer.store_name}
                  </span>
                )}
              </div>

              {/* Add to Basket Action */}
              <div className="pt-2 max-w-xs">
                {quantity > 0 ? (
                  <div className="flex items-center justify-between bg-emerald-600 text-white rounded-xl p-1 shadow-xs">
                    <button
                      onClick={() => updateQuantity(product.id, quantity - 1)}
                      className="w-8 h-8 rounded-lg bg-emerald-700/60 hover:bg-emerald-700 flex items-center justify-center transition-colors cursor-pointer"
                    >
                      {quantity === 1 ? <Trash2 className="w-4 h-4" /> : <Minus className="w-4 h-4" />}
                    </button>
                    <span className="text-xs font-black px-2">
                      {quantity} in Basket
                    </span>
                    <button
                      onClick={() => addItem(product)}
                      className="w-8 h-8 rounded-lg bg-emerald-700/60 hover:bg-emerald-700 flex items-center justify-center transition-colors cursor-pointer"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => addItem(product)}
                    className="w-full py-2.5 px-4 rounded-xl font-bold text-xs flex items-center justify-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-white transition-all cursor-pointer shadow-xs"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Add to Shopping Basket</span>
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Supermarket Comparison Matrix */}
          <div className="space-y-3 pt-2">
            <span className="text-2xs font-bold text-slate-500 uppercase tracking-wider block">
              Supermarket Price Matrix
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {sortedOffers.map((offer, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 flex items-center justify-between"
                >
                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <StoreBadge storeCode={offer.store_code} />
                      {idx === 0 && (
                        <span className="text-3xs font-black bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded">
                          BEST PRICE
                        </span>
                      )}
                    </div>
                    {offer.loyalty_card && (
                      <p className="text-3xs text-amber-800 font-semibold truncate">
                        Requires: {offer.loyalty_card}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center gap-3 text-right">
                    <div>
                      <p className="text-base font-black text-slate-900">
                        {formatPrice(offer.effective_price)} €
                      </p>
                      {offer.is_discount && Number(offer.price_regular) > Number(offer.effective_price) && (
                        <p className="text-2xs text-slate-400 line-through">
                          {formatPrice(offer.price_regular)} €
                        </p>
                      )}
                    </div>
                    <a
                      href={offer.product_url}
                      target="_blank"
                      rel="noreferrer"
                      className="p-1.5 rounded-lg bg-white border border-slate-200 text-slate-500 hover:text-slate-900 shadow-2xs"
                      title="Open store page"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Interactive Price History Chart */}
          <div className="pt-3 border-t border-slate-100">
            {loadingHistory ? (
              <div className="py-12 text-center flex flex-col items-center justify-center space-y-2">
                <RefreshCw className="w-6 h-6 text-emerald-600 animate-spin" />
                <p className="text-xs text-slate-400">Loading historical price records...</p>
              </div>
            ) : (
              <PriceHistoryChart history={history} />
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50/50 flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-slate-900 text-white font-bold text-xs hover:bg-slate-800 transition-colors"
          >
            Close Profile
          </button>
        </div>
      </div>
    </div>
  );
}
