// STS：商店資訊與評價
import { get, post } from '../api/client';
import type { Review, Store } from '../api/types';

export const listStores = () => get<Store[]>('/stores/');

export const getStore = (id: number) => get<Store>(`/stores/${id}`);

export const reviewStore = (storeId: number, data: { order_id: number; rating: number; comment?: string }) =>
  post<Review>(`/stores/${storeId}/reviews`, data);
