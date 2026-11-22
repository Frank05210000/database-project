// DMS：首頁顯示今天有效的優惠（公開端點）
import { get } from '../api/client';
import type { Discount } from '../api/types';

/** 端點尚未完成或出錯時回傳空陣列，首頁不因此壞掉 */
export const getActiveDiscounts = async (): Promise<Discount[]> => {
  try {
    const list = await get<Discount[]>('/discounts/active');
    return Array.isArray(list) ? list : [];
  } catch {
    return [];
  }
};
