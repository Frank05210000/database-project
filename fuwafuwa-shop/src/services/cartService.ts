// SCS：購物車存在伺服器端，每個寫入操作都回傳完整購物車與報價
import { del, get, post, put } from '../api/client';
import type { CartResponse } from '../api/types';

export const getCart = () => get<CartResponse>('/cart/');

export const addCartItem = (productId: number, quantity: number) =>
  post<CartResponse>('/cart/items', { product_id: productId, quantity });

export const updateCartItem = (productId: number, quantity: number) =>
  put<CartResponse>(`/cart/items/${productId}`, { quantity });

export const removeCartItem = (productId: number) => del<CartResponse>(`/cart/items/${productId}`);

export const clearCart = () => del<CartResponse>('/cart/');
