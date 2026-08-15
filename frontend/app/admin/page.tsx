"use client";

import React, { useEffect, useState } from "react";
import { ShieldCheck, Search, Edit3, Lock, RefreshCw, CheckCircle2, Image as ImageIcon } from "lucide-react";
import { AdminProduct, api } from "@/lib/api";
import { AdminEditModal } from "@/components/AdminEditModal";

export default function AdminPage() {
  const [products, setProducts] = useState<AdminProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [editingProduct, setEditingProduct] = useState<AdminProduct | null>(null);

  const loadCatalog = async () => {
    setLoading(true);
    try {
      const res = await api.getAdminProducts(page, search.trim() || undefined);
      setProducts(res.items);
      setTotalPages(res.total_pages);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCatalog();
  }, [page, search]);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-8 h-8 text-blue-600" />
            <span>Back-Office Catalog Curation</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Override master product details, lock fields from automated scraping overwrites, and upload high-res imagery.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="Search master products..."
            className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-slate-50/50"
          />
        </div>
        <button
          onClick={loadCatalog}
          className="p-2.5 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 cursor-pointer"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Catalog Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200/80 text-slate-500 font-bold uppercase tracking-wider">
              <tr>
                <th className="p-4">Image</th>
                <th className="p-4">Product Title</th>
                <th className="p-4">Brand</th>
                <th className="p-4">Unit</th>
                <th className="p-4">Curation Status</th>
                <th className="p-4">Locked Fields</th>
                <th className="p-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {loading ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-400">
                    Loading catalog...
                  </td>
                </tr>
              ) : products.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-400">
                    No products found.
                  </td>
                </tr>
              ) : (
                products.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="p-4">
                      <div className="w-12 h-12 rounded-xl bg-slate-50 border border-slate-100 p-1 flex items-center justify-center overflow-hidden">
                        {p.display_image_url ? (
                          <img
                            src={p.display_image_url}
                            alt={p.name_et}
                            className="w-full h-full object-contain mix-blend-multiply"
                          />
                        ) : (
                          <ImageIcon className="w-4 h-4 text-slate-300" />
                        )}
                      </div>
                    </td>
                    <td className="p-4">
                      <p className="font-bold text-slate-900 text-sm">{p.name_et}</p>
                      <p className="text-2xs text-slate-400 font-mono">EAN: {p.ean || "None"}</p>
                    </td>
                    <td className="p-4">
                      <span className="font-bold text-emerald-700">{p.brand || "-"}</span>
                    </td>
                    <td className="p-4">
                      <span className="text-slate-700">
                        {p.unit_amount} {p.unit_type}
                      </span>
                    </td>
                    <td className="p-4">
                      {p.is_manually_curated ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold text-2xs">
                          <CheckCircle2 className="w-3 h-3" />
                          Curated
                        </span>
                      ) : (
                        <span className="text-slate-400 text-2xs">Automated</span>
                      )}
                    </td>
                    <td className="p-4">
                      {p.locked_fields && p.locked_fields.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {p.locked_fields.map((f) => (
                            <span
                              key={f}
                              className="px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 text-3xs font-bold flex items-center gap-0.5"
                            >
                              <Lock className="w-2.5 h-2.5" />
                              {f}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-slate-400 text-2xs">None</span>
                      )}
                    </td>
                    <td className="p-4 text-right">
                      <button
                        onClick={() => setEditingProduct(p)}
                        className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-900 hover:text-white text-slate-700 font-bold text-xs inline-flex items-center gap-1.5 transition-colors cursor-pointer shadow-2xs"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                        <span>Curate</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-xs">
          <span className="text-slate-500 font-medium">
            Page {page} of {totalPages || 1}
          </span>
          <div className="flex gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-700 font-bold disabled:opacity-40"
            >
              Previous
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-700 font-bold disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Edit Modal */}
      {editingProduct && (
        <AdminEditModal
          product={editingProduct}
          onClose={() => setEditingProduct(null)}
          onSaved={loadCatalog}
        />
      )}
    </div>
  );
}
