import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from 'react';
import { useAuth } from './AuthContext';
import * as cartApi from '../services/cartService';
import type { CartResponse } from '../api/types';

interface CartContextType {
  /** 伺服器端購物車（未登入或非顧客時為 null） */
  cart: CartResponse | null;
  itemCount: number;
  loading: boolean;
  /** 目前使用者能否使用購物車（需要 customer 角色） */
  enabled: boolean;
  refresh: () => Promise<void>;
  /** 以下操作失敗時丟出 ApiError，讓頁面顯示後端訊息（例如 BR-06 超過庫存） */
  addToCart: (productId: number, quantity?: number) => Promise<void>;
  updateQuantity: (productId: number, quantity: number) => Promise<void>;
  removeItem: (productId: number) => Promise<void>;
  clearCart: () => Promise<void>;
  /** 下單後後端已清空購物車，前端同步歸零 */
  reset: () => void;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export const CartProvider = ({ children }: { children: ReactNode }) => {
  const { user, hasRole } = useAuth();
  const enabled = !!user && hasRole('customer');
  const [cart, setCart] = useState<CartResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    if (!enabled) {
      setCart(null);
      return;
    }
    setLoading(true);
    try {
      setCart(await cartApi.getCart());
    } catch {
      setCart(null);
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    refresh();
  }, [refresh, user?.user_id]);

  const addToCart = async (productId: number, quantity = 1) => {
    setCart(await cartApi.addCartItem(productId, quantity));
  };
  const updateQuantity = async (productId: number, quantity: number) => {
    setCart(await cartApi.updateCartItem(productId, quantity));
  };
  const removeItem = async (productId: number) => {
    setCart(await cartApi.removeCartItem(productId));
  };
  const clearCart = async () => {
    setCart(await cartApi.clearCart());
  };
  const reset = () => setCart((c) => (c ? { ...c, items: [] } : c));

  const itemCount = cart?.items.reduce((sum, i) => sum + i.quantity, 0) ?? 0;

  return (
    <CartContext.Provider
      value={{ cart, itemCount, loading, enabled, refresh, addToCart, updateQuantity, removeItem, clearCart, reset }}
    >
      {children}
    </CartContext.Provider>
  );
};

export const useCartContext = () => {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error('useCart must be used within a CartProvider');
  return ctx;
};
