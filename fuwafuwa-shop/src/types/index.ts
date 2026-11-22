// 資料型別一律以 src/api/types.ts（API 契約）為準，這裡只補前端自用的型別。
export type {
  Product,
  Store,
  Review,
  CartLine,
  CartResponse,
  Quote,
  Order,
  OrderSummary,
  OrderStatus,
  ReturnRequest,
  Discount,
} from '../api/types';

/** 寵物看到商品時的反應（純裝飾用） */
export type ReactionType = 'hungry' | 'excited' | 'happy' | 'curious' | 'neutral';

/** 商品分類（與資料庫 product.category 一致） */
export type Category = 'food' | 'toy' | 'accessory' | 'care' | 'home';

export const CATEGORIES: Category[] = ['food', 'toy', 'accessory', 'care', 'home'];
