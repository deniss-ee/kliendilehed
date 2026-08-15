import React from "react";

interface StoreBadgeProps {
  storeCode: string;
  size?: "sm" | "md";
}

export const STORE_COLORS: Record<string, { bg: string; text: string; label: string }> = {
  SELVER: { bg: "bg-red-50 border-red-200 text-red-700", text: "text-red-700", label: "Selver" },
  RIMI: { bg: "bg-rose-50 border-rose-200 text-rose-700", text: "text-rose-700", label: "Rimi" },
  PRISMA: { bg: "bg-emerald-50 border-emerald-200 text-emerald-700", text: "text-emerald-700", label: "Prisma" },
  COOP: { bg: "bg-blue-50 border-blue-200 text-blue-700", text: "text-blue-700", label: "Coop" },
  MAXIMA: { bg: "bg-indigo-50 border-indigo-200 text-indigo-700", text: "text-indigo-700", label: "Maxima" },
  GROSSI: { bg: "bg-amber-50 border-amber-200 text-amber-700", text: "text-amber-700", label: "Grossi" },
  LIDL: { bg: "bg-sky-50 border-sky-200 text-sky-700", text: "text-sky-700", label: "Lidl" },
};

export function StoreBadge({ storeCode, size = "md" }: StoreBadgeProps) {
  const meta = STORE_COLORS[storeCode.toUpperCase()] || {
    bg: "bg-slate-50 border-slate-200 text-slate-700",
    text: "text-slate-700",
    label: storeCode,
  };

  const sizeClass = size === "sm" ? "px-1.5 py-0.5 text-xs font-semibold" : "px-2.5 py-1 text-xs font-bold";

  return (
    <span className={`inline-flex items-center rounded-md border ${meta.bg} ${sizeClass} tracking-wide shadow-2xs`}>
      {meta.label}
    </span>
  );
}
