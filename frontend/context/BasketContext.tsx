"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { ProductItem } from "@/lib/api";

export interface BasketItem {
  product: ProductItem;
  quantity: number;
}

export const DEFAULT_LOYALTY_CARDS = [
  "Partnerkaart",
  "Rimi kaart",
  "Säästukaart",
  "Aitäh kaart",
  "Lidl Plus",
];

interface BasketContextType {
  basket: BasketItem[];
  loyaltyCards: string[];
  isLoaded: boolean;
  addItem: (product: ProductItem) => void;
  removeItem: (productId: string) => void;
  updateQuantity: (productId: string, quantity: number) => void;
  clearBasket: () => void;
  toggleLoyaltyCard: (card: string) => void;
  getItemQuantity: (productId: string) => number;
  totalItemCount: number;
}

const BASKET_STORAGE_KEY = "kliendilehed_basket_v2";
const LOYALTY_STORAGE_KEY = "kliendilehed_loyalty_cards_v2";

const BasketContext = createContext<BasketContextType | undefined>(undefined);

export function BasketProvider({ children }: { children: ReactNode }) {
  const [basket, setBasket] = useState<BasketItem[]>([]);
  const [loyaltyCards, setLoyaltyCards] = useState<string[]>(DEFAULT_LOYALTY_CARDS);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    try {
      const savedBasket = localStorage.getItem(BASKET_STORAGE_KEY);
      if (savedBasket) {
        setBasket(JSON.parse(savedBasket));
      }
      const savedLoyalty = localStorage.getItem(LOYALTY_STORAGE_KEY);
      if (savedLoyalty) {
        setLoyaltyCards(JSON.parse(savedLoyalty));
      }
    } catch (e) {
      console.error("Error loading basket state:", e);
    }
    setIsLoaded(true);
  }, []);

  const saveBasket = (newBasket: BasketItem[]) => {
    setBasket(newBasket);
    try {
      localStorage.setItem(BASKET_STORAGE_KEY, JSON.stringify(newBasket));
    } catch (e) {
      console.error(e);
    }
  };

  const addItem = (product: ProductItem) => {
    setBasket((prev) => {
      const existing = prev.find((item) => item.product.id === product.id);
      let updated: BasketItem[];
      if (existing) {
        updated = prev.map((item) =>
          item.product.id === product.id ? { ...item, quantity: item.quantity + 1 } : item
        );
      } else {
        updated = [...prev, { product, quantity: 1 }];
      }
      try {
        localStorage.setItem(BASKET_STORAGE_KEY, JSON.stringify(updated));
      } catch (e) {}
      return updated;
    });
  };

  const removeItem = (productId: string) => {
    setBasket((prev) => {
      const updated = prev.filter((item) => item.product.id !== productId);
      try {
        localStorage.setItem(BASKET_STORAGE_KEY, JSON.stringify(updated));
      } catch (e) {}
      return updated;
    });
  };

  const updateQuantity = (productId: string, quantity: number) => {
    if (quantity <= 0) {
      removeItem(productId);
      return;
    }
    setBasket((prev) => {
      const updated = prev.map((item) =>
        item.product.id === productId ? { ...item, quantity } : item
      );
      try {
        localStorage.setItem(BASKET_STORAGE_KEY, JSON.stringify(updated));
      } catch (e) {}
      return updated;
    });
  };

  const clearBasket = () => {
    setBasket([]);
    try {
      localStorage.setItem(BASKET_STORAGE_KEY, JSON.stringify([]));
    } catch (e) {}
  };

  const toggleLoyaltyCard = (card: string) => {
    setLoyaltyCards((prev) => {
      const updated = prev.includes(card)
        ? prev.filter((c) => c !== card)
        : [...prev, card];
      try {
        localStorage.setItem(LOYALTY_STORAGE_KEY, JSON.stringify(updated));
      } catch (e) {}
      return updated;
    });
  };

  const getItemQuantity = (productId: string): number => {
    const it = basket.find((i) => i.product.id === productId);
    return it ? it.quantity : 0;
  };

  const totalItemCount = basket.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <BasketContext.Provider
      value={{
        basket,
        loyaltyCards,
        isLoaded,
        addItem,
        removeItem,
        updateQuantity,
        clearBasket,
        toggleLoyaltyCard,
        getItemQuantity,
        totalItemCount,
      }}
    >
      {children}
    </BasketContext.Provider>
  );
}

export function useBasket() {
  const context = useContext(BasketContext);
  if (!context) {
    throw new Error("useBasket must be used within a BasketProvider");
  }
  return context;
}
