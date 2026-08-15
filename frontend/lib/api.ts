const API_BASE = "/api";

export interface StoreOffer {
  store_code: string;
  store_name: string;
  price_regular: number;
  price_discount: number | null;
  price_loyalty: number | null;
  effective_price: number;
  is_discount: boolean;
  loyalty_card: string | null;
  product_url: string;
}

export interface ProductItem {
  id: string;
  ean: string | null;
  name: string;
  brand: string | null;
  unit: string;
  package_quantity: number;
  image_url: string | null;
  min_price: number | null;
  has_discount: boolean;
  store_count: number;
  offers: StoreOffer[];
}

export interface SearchResponse {
  items: ProductItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface BasketItemQuote {
  store_code: string;
  store_name: string;
  product_title: string;
  regular_price: number;
  effective_price: number;
  is_discount: boolean;
  loyalty_card_used: string | null;
  product_url: string;
}

export interface OptimizedItem {
  canonical_product_id: string;
  canonical_name: string;
  quantity: number;
  quotes_by_store: Record<string, BasketItemQuote>;
  cheapest_store: string;
  cheapest_price: number;
}

export interface SingleStoreRanking {
  store_code: string;
  store_name: string;
  available_items_count: number;
  missing_items_count: number;
  total_cost: number;
  regular_total_cost: number;
  total_savings: number;
  missing_item_names: string[];
}

export interface SplitRouteItem {
  canonical_id: string;
  name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  product_url: string;
}

export interface BasketOptimizationResponse {
  total_requested_items: number;
  items_analyzed: OptimizedItem[];
  single_store_rankings: SingleStoreRanking[];
  cheapest_single_store: SingleStoreRanking | null;
  optimized_split_route: {
    total_cost: number;
    savings_vs_best_single: number;
    store_breakdown: Record<string, SplitRouteItem[]>;
  };
  total_loyalty_savings: number;
}

export interface AdminProduct {
  id: string;
  ean: string | null;
  name_et: string;
  brand: string | null;
  category_path: string[] | null;
  unit_amount: number;
  unit_type: string;
  package_quantity: number;
  display_image_url: string | null;
  custom_image_url: string | null;
  is_manually_curated: boolean;
  locked_fields: string[];
  updated_at: string;
}

export const api = {
  async searchProducts(params?: {
    query?: string;
    brand?: string;
    store?: string;
    on_sale_only?: boolean;
    page?: number;
  }): Promise<SearchResponse> {
    const query = new URLSearchParams();
    if (params?.query) query.set("query", params.query);
    if (params?.brand) query.set("brand", params.brand);
    if (params?.store) query.set("store", params.store);
    if (params?.on_sale_only) query.set("on_sale_only", "true");
    if (params?.page) query.set("page", params.page.toString());

    const res = await fetch(`${API_BASE}/products/search?${query.toString()}`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch products");
    return res.json();
  },

  async getDeals(limit = 30): Promise<any[]> {
    const res = await fetch(`${API_BASE}/deals?limit=${limit}`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch deals");
    return res.json();
  },

  async optimizeBasket(items: { canonical_product_id: string; quantity: number }[], loyaltyCards: string[]): Promise<BasketOptimizationResponse> {
    const res = await fetch(`${API_BASE}/basket/optimize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        items,
        user_loyalty_cards: loyaltyCards,
      }),
    });
    if (!res.ok) throw new Error("Failed to optimize basket");
    return res.json();
  },

  // Admin Endpoints
  async getAdminProducts(page = 1, query?: string): Promise<{ items: AdminProduct[]; total: number; total_pages: number }> {
    const url = new URLSearchParams({ page: page.toString() });
    if (query) url.set("query", query);
    const res = await fetch(`${API_BASE}/admin/products?${url.toString()}`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch admin products");
    return res.json();
  },

  async overrideProduct(id: string, data: any): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/products/${id}/override`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update product");
    return res.json();
  },

  async uploadProductImage(id: string, file: File): Promise<{ image_url: string }> {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE}/admin/products/${id}/image`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) throw new Error("Failed to upload image");
    return res.json();
  },
};
