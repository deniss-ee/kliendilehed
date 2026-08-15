"use client";

import React, { useState } from "react";
import { STORE_COLORS } from "./StoreBadge";

export interface PricePoint {
  store_code: string;
  store_name: string;
  price_regular: number;
  price_discount: number | null;
  price_loyalty: number | null;
  recorded_at: string;
}

interface PriceHistoryChartProps {
  history: PricePoint[];
}

export function PriceHistoryChart({ history }: PriceHistoryChartProps) {
  const [hoveredPoint, setHoveredPoint] = useState<{
    date: string;
    store: string;
    price: number;
    isDiscount: boolean;
    x: number;
    y: number;
  } | null>(null);

  if (!history || history.length === 0) {
    return (
      <div className="py-12 text-center text-slate-400 text-xs bg-slate-50/50 rounded-2xl border border-slate-100">
        No price history recorded yet for this product.
      </div>
    );
  }

  // Group price points by store
  const byStore: Record<string, PricePoint[]> = {};
  history.forEach((pt) => {
    const code = pt.store_code.toUpperCase();
    if (!byStore[code]) byStore[code] = [];
    byStore[code].push(pt);
  });

  // Sort each store points chronologically
  Object.keys(byStore).forEach((code) => {
    byStore[code].sort((a, b) => new Date(a.recorded_at).getTime() - new Date(b.recorded_at).getTime());
  });

  // Compute overall min & max price for Y-axis scaling
  const allPrices = history.map(
    (h) => h.price_loyalty || h.price_discount || h.price_regular
  );
  const minPrice = Math.max(0, Math.min(...allPrices) * 0.9);
  const maxPrice = Math.max(...allPrices) * 1.1;
  const priceRange = maxPrice - minPrice || 1;

  // Chart dimensions
  const width = 600;
  const height = 220;
  const paddingLeft = 45;
  const paddingRight = 20;
  const paddingTop = 20;
  const paddingBottom = 30;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  // Find overall time range for X-axis
  const allTimestamps = history.map((h) => new Date(h.recorded_at).getTime());
  const minTime = Math.min(...allTimestamps);
  const maxTime = Math.max(...allTimestamps);
  const timeRange = maxTime - minTime || 1;

  const getX = (dateStr: string) => {
    const t = new Date(dateStr).getTime();
    return paddingLeft + ((t - minTime) / timeRange) * chartWidth;
  };

  const getY = (price: number) => {
    return paddingTop + chartHeight - ((price - minPrice) / priceRange) * chartHeight;
  };

  const STORE_STROKES: Record<string, string> = {
    SELVER: "#d9251d",
    PRISMA: "#00823b",
    COOP: "#004b92",
    RIMI: "#e30613",
    MAXIMA: "#002d72",
    LIDL: "#0050aa",
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-2xs font-bold text-slate-500 uppercase tracking-wider">
          60-Day Price Trend by Store
        </span>
        <div className="flex items-center gap-3">
          {Object.keys(byStore).map((code) => {
            const color = STORE_STROKES[code] || "#64748b";
            return (
              <div key={code} className="flex items-center gap-1.5 text-2xs font-semibold text-slate-600">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                <span>{code}</span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="relative w-full overflow-hidden bg-slate-50/70 rounded-2xl border border-slate-200/80 p-3">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto overflow-visible">
          {/* Horizontal Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((fraction, idx) => {
            const pVal = minPrice + fraction * priceRange;
            const y = paddingTop + chartHeight - fraction * chartHeight;
            return (
              <g key={idx}>
                <line
                  x1={paddingLeft}
                  y1={y}
                  x2={width - paddingRight}
                  y2={y}
                  stroke="#e2e8f0"
                  strokeDasharray="3 3"
                />
                <text
                  x={paddingLeft - 8}
                  y={y + 3}
                  textAnchor="end"
                  fontSize="9"
                  fill="#94a3b8"
                  fontWeight="600"
                >
                  {pVal.toFixed(2)}€
                </text>
              </g>
            );
          })}

          {/* Render Lines for each store */}
          {Object.entries(byStore).map(([storeCode, points]) => {
            const strokeColor = STORE_STROKES[storeCode] || "#64748b";

            const pathD = points
              .map((pt, i) => {
                const eff = pt.price_loyalty || pt.price_discount || pt.price_regular;
                const x = getX(pt.recorded_at);
                const y = getY(eff);
                return `${i === 0 ? "M" : "L"} ${x} ${y}`;
              })
              .join(" ");

            return (
              <g key={storeCode}>
                {/* Line Path */}
                <path
                  d={pathD}
                  fill="none"
                  stroke={strokeColor}
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />

                {/* Data Points */}
                {points.map((pt, idx) => {
                  const eff = pt.price_loyalty || pt.price_discount || pt.price_regular;
                  const x = getX(pt.recorded_at);
                  const y = getY(eff);
                  const isDisc = Boolean(pt.price_discount || pt.price_loyalty);

                  return (
                    <circle
                      key={idx}
                      cx={x}
                      cy={y}
                      r={isDisc ? "4.5" : "3.5"}
                      fill={isDisc ? "#ef4444" : "#ffffff"}
                      stroke={strokeColor}
                      strokeWidth="2"
                      className="cursor-pointer transition-transform hover:scale-150"
                      onMouseEnter={() =>
                        setHoveredPoint({
                          date: new Date(pt.recorded_at).toLocaleDateString("et-EE"),
                          store: storeCode,
                          price: eff,
                          isDiscount: isDisc,
                          x,
                          y,
                        })
                      }
                      onMouseLeave={() => setHoveredPoint(null)}
                    />
                  );
                })}
              </g>
            );
          })}
        </svg>

        {/* Hover Tooltip */}
        {hoveredPoint && (
          <div
            className="absolute z-20 pointer-events-none bg-slate-900 text-white text-2xs px-2.5 py-1.5 rounded-lg shadow-lg -translate-x-1/2 -translate-y-full mb-2 font-medium"
            style={{
              left: `${(hoveredPoint.x / width) * 100}%`,
              top: `${(hoveredPoint.y / height) * 100}%`,
            }}
          >
            <p className="font-bold text-emerald-400">
              {hoveredPoint.store}: {hoveredPoint.price.toFixed(2)} €
            </p>
            <p className="text-3xs text-slate-300">{hoveredPoint.date}</p>
            {hoveredPoint.isDiscount && (
              <span className="text-3xs text-red-300 font-bold">Promotion / Discount</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
