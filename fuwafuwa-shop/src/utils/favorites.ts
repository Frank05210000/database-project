// 「我的最愛」只存在瀏覽器（裝飾性功能，不經過後端）
const KEY = 'favoriteProducts';

export const readFavorites = (): number[] => {
  try {
    const raw = localStorage.getItem(KEY);
    const list = raw ? JSON.parse(raw) : [];
    return Array.isArray(list) ? list.map(Number).filter((n) => Number.isFinite(n)) : [];
  } catch {
    return [];
  }
};

export const toggleFavorite = (productId: number): boolean => {
  const list = readFavorites();
  const on = !list.includes(productId);
  const next = on ? [...list, productId] : list.filter((id) => id !== productId);
  try {
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    /* ignore */
  }
  return on;
};
