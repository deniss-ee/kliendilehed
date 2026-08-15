"use client";

import React, { useState } from "react";
import { Plus, Minus, Trash2, ExternalLink, Tag, ShoppingBasket, LineChart } from "lucide-react";
import { ProductItem } from "@/lib/api";
import { StoreBadge } from "./StoreBadge";
import { ProductDetailModal } from "./ProductDetailModal";
import { useBasket } from "@/lib/store";

interface ProductCardProps {
  product: ProductItem;
}

const formatPrice = (val: any): string => {
  const num = typeof val === "number" ? val : parseFloat(val || "0");
  return isNaN(num) ? "0.00" : num.toFixed(2);
};

export function ProductCard({ product }: ProductCardProps) {
  const [showModal, setShowModal] = useState(false);
  const { addItem, updateQuantity, removeItem, getItemQuantity } = useBasket();
  const quantity = getItemQuantity(product.id);

  // Sort offers by effective price ascending
  const sortedOffers = [...product.offers].sort(
    (a, b) => (Number(a.effective_price) || 0) - (Number(b.effective_price) || 0)
  );
  const bestOffer = sortedOffers[0];

  return (
    <>
      <div className="bg-white rounded-2xl border border-slate-200/80 hover:border-slate-300 shadow-xs hover:shadow-md transition-all flex flex-col overflow-hidden group">
        {/* Image & Badges (Click to open details) */}
        <div
          onClick={() => setShowModal(true)}
          className="relative aspect-square w-full bg-slate-50 flex items-center justify-center p-4 overflow-hidden border-b border-slate-100 cursor-pointer"
        >
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="w-full h-full object-contain mix-blend-multiply group-hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
          ) : (
            <div className="text-slate-300 text-sm font-medium">No Image Available</div>
          )}

          {/* Discount Badge */}
          {product.has_discount && (
            <div className="absolute top-3 left-3 bg-red-600 text-white text-xs font-black px-2.5 py-1 rounded-full shadow-xs flex items-center gap-1 animate-pulse">
              <Tag className="w-3 h-3" />
              <span>SALE</span>
            </div>
          )}

          {/* Unit Amount Badge */}
          <div className="absolute bottom-3 right-3 bg-slate-900/80 backdrop-blur-xs text-white text-xs font-semibold px-2 py-0.5 rounded-md">
            {product.unit}
          </div>

          {/* Chart quick hover cue */}
          <div
            className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 bg-white/90 backdrop-blur-xs text-slate-700 p-1.5 rounded-lg shadow-xs transition-opacity"
            title="View Price Trend"
          >
            <LineChart className="w-3.5 h-3.5 text-emerald-600" />
          </div>
        </div>

        {/* Content */}
        <div className="p-4 flex-1 flex flex-col justify-between">
          <div>
            {/* Brand */}
            {product.brand && (
              <span className="text-xs font-bold text-emerald-700 uppercase tracking-wider block mb-1">
                {product.brand}
              </span>
            )}

            {/* Title (Click to open details) */}
            <h3
              onClick={() => setShowModal(true)}
              className="font-semibold text-slate-900 text-sm line-clamp-2 leading-snug cursor-pointer hover:text-emerald-700 transition-colors"
              title={product.name}
            >
              {product.name}
            </h3>

            {/* Best Price Header */}
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-black text-slate-900">
                {bestOffer ? `${formatPrice(bestOffer.effective_price)} €` : "-"}
              </span>
              {bestOffer &&
                bestOffer.is_discount &&
                Number(bestOffer.price_regular) > Number(bestOffer.effective_price) && (
                  <span className="text-sm font-semibold text-slate-400 line-through">
                    {formatPrice(bestOffer.price_regular)} €
                  </span>
                )}
            </div>
          </div>

          {/* Multi-Store Comparison Table */}
          <div className="mt-4 pt-3 border-t border-slate-100">
            <span className="text-2xs font-bold text-slate-500 uppercase tracking-wider block mb-2">
              Store Availability ({product.offers.length})
            </span>
            <div className="space-y-1.5 max-h-32 overflow-y-auto pr-1">
              {sortedOffers.map((offer, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between text-xs py-1 px-2 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-center gap-1.5 min-w-0">
                    <StoreBadge storeCode={offer.store_code} size="sm" />
                    {offer.loyalty_card && (
                      <span className="text-3xs bg-amber-100 text-amber-900 font-semibold px-1 rounded truncate">
                        {offer.loyalty_card}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`font-bold ${
                        idx === 0 ? "text-emerald-700" : "text-slate-700"
                      }`}
                    >
                      {formatPrice(offer.effective_price)} €
                    </span>
                    <a
                      href={offer.product_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-slate-400 hover:text-slate-600"
                      title="View in store"
                    >
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Action: Stepper / Add */}
          <div className="mt-4">
            {quantity > 0 ? (
              <div className="flex items-center justify-between bg-emerald-600 text-white rounded-xl p-1 shadow-xs animate-in fade-in zoom-in-95 duration-150">
                <button
                  onClick={() => updateQuantity(product.id, quantity - 1)}
                  className="w-8 h-8 rounded-lg bg-emerald-700/60 hover:bg-emerald-700 flex items-center justify-center transition-colors cursor-pointer"
                  title={quantity === 1 ? "Remove from basket" : "Decrease quantity"}
                >
                  {quantity === 1 ? <Trash2 className="w-4 h-4" /> : <Minus className="w-4 h-4" />}
                </button>

                <span className="text-xs font-black tracking-wide flex items-center gap-1.5 px-2">
                  <ShoppingBasket className="w-3.5 h-3.5" />
                  <span>{quantity} in Basket</span>
                </span>

                <button
                  onClick={() => addItem(product)}
                  className="w-8 h-8 rounded-lg bg-emerald-700/60 hover:bg-emerald-700 flex items-center justify-center transition-colors cursor-pointer"
                  title="Add one more"
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
                <span>Add to Basket</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Product Detail Modal */}
      {showModal && (
        <ProductDetailModal
          product={product}
          onClose={() => setShowModal(false)}
        />
      )}
    </>
  );
}
