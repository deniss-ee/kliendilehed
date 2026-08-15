"use client";

import React, { useState } from "react";
import { X, Lock, Upload, Save, CheckCircle2 } from "lucide-react";
import { AdminProduct, api } from "@/lib/api";

interface AdminEditModalProps {
  product: AdminProduct;
  onClose: () => void;
  onSaved: () => void;
}

export function AdminEditModal({ product, onClose, onSaved }: AdminEditModalProps) {
  const [name, setName] = useState(product.name_et);
  const [brand, setBrand] = useState(product.brand || "");
  const [unitAmount, setUnitAmount] = useState(product.unit_amount.toString());
  const [unitType, setUnitType] = useState(product.unit_type);
  const [lockedFields, setLockedFields] = useState<string[]>(product.locked_fields || []);
  const [customImageUrl, setCustomImageUrl] = useState(product.custom_image_url || "");
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  const toggleLock = (field: string) => {
    setLockedFields((prev) =>
      prev.includes(field) ? prev.filter((f) => f !== field) : [...prev, field]
    );
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const res = await api.uploadProductImage(product.id, file);
      setCustomImageUrl(res.image_url);
      if (!lockedFields.includes("custom_image_url")) {
        setLockedFields((prev) => [...prev, "custom_image_url"]);
      }
    } catch (err) {
      alert("Failed to upload image.");
    } finally {
      setUploading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.overrideProduct(product.id, {
        name_et: name,
        brand: brand || null,
        unit_amount: parseFloat(unitAmount),
        unit_type: unitType,
        custom_image_url: customImageUrl || null,
        lock_fields: lockedFields,
      });
      setSuccess(true);
      setTimeout(() => {
        onSaved();
        onClose();
      }, 800);
    } catch (err) {
      alert("Failed to save overrides.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl max-w-2xl w-full border border-slate-200 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Curate Master Product</h2>
            <p className="text-xs text-slate-500">ID: {product.id}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          {/* Title with Lock */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-bold text-slate-700 uppercase">Canonical Estonian Title</label>
              <button
                type="button"
                onClick={() => toggleLock("name_et")}
                className={`text-2xs font-bold px-2 py-0.5 rounded-md flex items-center gap-1 transition-colors ${
                  lockedFields.includes("name_et")
                    ? "bg-amber-100 text-amber-800 border border-amber-300"
                    : "bg-slate-100 text-slate-500"
                }`}
              >
                <Lock className="w-3 h-3" />
                {lockedFields.includes("name_et") ? "Field Locked" : "Lock Field"}
              </button>
            </div>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>

          {/* Brand & Units Row */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-bold text-slate-700 uppercase">Brand</label>
                <button
                  type="button"
                  onClick={() => toggleLock("brand")}
                  className={`text-3xs font-bold px-1.5 py-0.5 rounded ${
                    lockedFields.includes("brand") ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-500"
                  }`}
                >
                  <Lock className="w-2.5 h-2.5" />
                </button>
              </div>
              <input
                type="text"
                value={brand}
                onChange={(e) => setBrand(e.target.value)}
                placeholder="e.g. Tere, Alma"
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 uppercase block mb-1.5">Unit Amount</label>
              <input
                type="number"
                step="0.001"
                value={unitAmount}
                onChange={(e) => setUnitAmount(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 uppercase block mb-1.5">Unit Metric</label>
              <select
                value={unitType}
                onChange={(e) => setUnitType(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
              >
                <option value="kg">kg (Kilogram)</option>
                <option value="l">l (Liter)</option>
                <option value="piece">piece (Count)</option>
              </select>
            </div>
          </div>

          {/* High-Resolution Photo Upload */}
          <div className="pt-2 border-t border-slate-100">
            <label className="text-xs font-bold text-slate-700 uppercase block mb-2">
              High-Resolution Product Image
            </label>
            <div className="flex items-center gap-4">
              <div className="w-20 h-20 rounded-xl bg-slate-100 border border-slate-200 p-2 flex items-center justify-center overflow-hidden">
                {customImageUrl || product.display_image_url ? (
                  <img
                    src={customImageUrl || product.display_image_url!}
                    alt="Preview"
                    className="w-full h-full object-contain"
                  />
                ) : (
                  <span className="text-3xs text-slate-400">No Image</span>
                )}
              </div>
              <div className="flex-1">
                <label className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs cursor-pointer transition-colors border border-slate-200">
                  <Upload className="w-4 h-4" />
                  <span>{uploading ? "Uploading..." : "Upload New High-Res Photo"}</span>
                  <input type="file" accept="image/*" onChange={handleFileUpload} className="hidden" />
                </label>
                <p className="text-2xs text-slate-400 mt-1">
                  Saved to local MinIO/static storage. Overwrites low-res store thumbnails.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50/50 flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-slate-600 font-semibold text-xs hover:bg-slate-100"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving || success}
            className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-emerald-500/20 disabled:opacity-50 transition-all cursor-pointer"
          >
            {success ? (
              <>
                <CheckCircle2 className="w-4 h-4" />
                <span>Saved!</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>{saving ? "Saving..." : "Save Overrides"}</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
