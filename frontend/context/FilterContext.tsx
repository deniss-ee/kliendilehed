"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";
import { CATEGORIES } from "@/lib/categories";

interface FilterContextType {
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  selectedStores: string[];
  toggleStore: (storeCode: string) => void;
  clearStores: () => void;
  selectedCategories: string[];
  toggleCategory: (categoryId: string) => void;
  clearCategories: () => void;
  onSaleOnly: boolean;
  setOnSaleOnly: (val: boolean) => void;
  toggleOnSaleOnly: () => void;
  resetAllFilters: () => void;
  hasActiveFilters: boolean;
  getKeywordsQuery: () => string;
}

const FilterContext = createContext<FilterContextType | undefined>(undefined);

export function FilterProvider({ children }: { children: ReactNode }) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedStores, setSelectedStores] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [onSaleOnly, setOnSaleOnly] = useState(false);

  const toggleStore = (storeCode: string) => {
    const code = storeCode.toUpperCase();
    setSelectedStores((prev) =>
      prev.includes(code) ? prev.filter((s) => s !== code) : [...prev, code]
    );
  };

  const clearStores = () => setSelectedStores([]);

  const toggleCategory = (catId: string) => {
    if (catId === "all") {
      setSelectedCategories([]);
      return;
    }
    setSelectedCategories((prev) =>
      prev.includes(catId) ? prev.filter((c) => c !== catId) : [...prev, catId]
    );
  };

  const clearCategories = () => setSelectedCategories([]);

  const toggleOnSaleOnly = () => setOnSaleOnly((prev) => !prev);

  const resetAllFilters = () => {
    setSearchQuery("");
    setSelectedStores([]);
    setSelectedCategories([]);
    setOnSaleOnly(false);
  };

  const hasActiveFilters =
    searchQuery.trim().length > 0 ||
    selectedStores.length > 0 ||
    selectedCategories.length > 0 ||
    onSaleOnly;

  // Build combined keyword query for all active selected categories + custom search
  const getKeywordsQuery = (): string => {
    const parts: string[] = [];
    if (searchQuery.trim()) {
      parts.push(searchQuery.trim());
    }

    if (selectedCategories.length > 0) {
      for (const catId of selectedCategories) {
        const cat = CATEGORIES.find((c) => c.id === catId);
        if (cat && cat.keywords.length > 0) {
          // Add primary keywords from the category
          parts.push(cat.keywords.slice(0, 3).join(" "));
        }
      }
    }

    return parts.join(" ");
  };

  return (
    <FilterContext.Provider
      value={{
        searchQuery,
        setSearchQuery,
        selectedStores,
        toggleStore,
        clearStores,
        selectedCategories,
        toggleCategory,
        clearCategories,
        onSaleOnly,
        setOnSaleOnly,
        toggleOnSaleOnly,
        resetAllFilters,
        hasActiveFilters,
        getKeywordsQuery,
      }}
    >
      {children}
    </FilterContext.Provider>
  );
}

export function useFilters() {
  const context = useContext(FilterContext);
  if (!context) {
    throw new Error("useFilters must be used within a FilterProvider");
  }
  return context;
}
