import type { SyntheticEvent } from 'react';
import type { EventDiscount } from '../api/types';
import type { ReactionType } from '../types';

const CATEGORY_IMAGE: Record<string, string> = {
  food: 'can.png',
  toy: 'ball.png',
  accessory: 'collar.png',
  care: 'brush.png',
  home: 'cage.png',
};

/** 分類圖示（篩選按鈕、徽章、圖片載入失敗時的備用圖） */
export const categoryImage = (category: string | null | undefined): string =>
  `/images/${CATEGORY_IMAGE[category ?? ''] ?? 'All.png'}`;

export const productImage = (p: { image_url: string | null; category?: string | null }): string =>
  p.image_url || categoryImage(p.category);

/** <img onError> 用：商品圖不存在時改顯示分類圖示 */
export const imageFallback = (category: string | null | undefined) => (e: SyntheticEvent<HTMLImageElement>) => {
  const img = e.currentTarget;
  const fallback = categoryImage(category);
  if (!img.src.endsWith(fallback)) img.src = fallback;
};

export const reactionFor = (category: string | null | undefined): ReactionType => {
  switch (category) {
    case 'food':
      return 'hungry';
    case 'toy':
      return 'excited';
    case 'care':
    case 'accessory':
      return 'happy';
    default:
      return 'curious';
  }
};

/** 特殊活動折扣的簡短說明，例如「9 折」或「買 2 送 1」 */
export const eventBadge = (ev: EventDiscount | null | undefined, lang: 'zh' | 'en' = 'zh'): string | null => {
  if (!ev) return null;
  if (ev.buy_qty && ev.free_qty) {
    return lang === 'zh' ? `買 ${ev.buy_qty} 送 ${ev.free_qty}` : `Buy ${ev.buy_qty} get ${ev.free_qty}`;
  }
  if (ev.rate != null) {
    // rate 是折抵比例：0.2 → 8 折、0.15 → 85 折
    const r = Number(ev.rate);
    if (lang === 'en') return `${Math.round(r * 100)}% OFF`;
    const pct = Math.round((1 - r) * 100);
    return `${pct % 10 === 0 ? pct / 10 : pct} 折`;
  }
  return lang === 'zh' ? '活動中' : 'On sale';
};
