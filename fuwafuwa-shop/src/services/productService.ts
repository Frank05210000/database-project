// PMS：商品瀏覽與搜尋（US-01）
import { get } from '../api/client';
import type { Product } from '../api/types';

export type ProductSort = 'newest' | 'price_asc' | 'price_desc';

export interface ProductQuery {
  q?: string;
  category?: string;
  store_id?: number;
  sort?: ProductSort;
}

export const listProducts = (query: ProductQuery = {}) =>
  get<Product[]>('/products/', { ...query });

export const getProduct = (id: number) => get<Product>(`/products/${id}`);

export const listCategories = () => get<string[]>('/products/categories');
