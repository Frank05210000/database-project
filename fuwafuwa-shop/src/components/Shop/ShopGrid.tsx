import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import type { Product, Store } from '../../api/types';
import { errorMessage } from '../../api/client';
import { CATEGORIES, Category } from '../../types';
import { useLanguage } from '../../i18n';
import { listProducts, ProductSort } from '../../services/productService';
import { listStores } from '../../services/storeService';
import { readFavorites } from '../../utils/favorites';
import { ProductCard } from './ProductCard';
import './ShopGrid.css';

interface ShopGridProps {
  onProductClick?: (product: Product) => void;
  /** 標題列上方的額外內容（例如優惠橫幅） */
  banner?: React.ReactNode;
}

type CategoryFilter = 'all' | Category | 'favorites';
const FILTERS: CategoryFilter[] = ['all', ...CATEGORIES, 'favorites'];

/** 商品列表：關鍵字搜尋（US-01）、分類、商店、排序全部交給後端 GET /api/products */
export const ShopGrid: React.FC<ShopGridProps> = ({ onProductClick, banner }) => {
  const { t } = useLanguage();
  const [params, setParams] = useSearchParams();
  const q = params.get('q') ?? '';
  const storeId = params.get('store') ?? '';
  const sort = (params.get('sort') as ProductSort) || 'newest';
  const selectedCategory = (params.get('category') as CategoryFilter) || 'all';

  const [keyword, setKeyword] = useState(q);
  const [products, setProducts] = useState<Product[]>([]);
  const [stores, setStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => setKeyword(q), [q]);

  useEffect(() => {
    listStores().then(setStores).catch(() => setStores([]));
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    listProducts({
      q: q || undefined,
      category: selectedCategory !== 'all' && selectedCategory !== 'favorites' ? selectedCategory : undefined,
      store_id: storeId ? Number(storeId) : undefined,
      sort,
    })
      .then((list) => {
        if (cancelled) return;
        setProducts(selectedCategory === 'favorites' ? list.filter((p) => readFavorites().includes(p.product_id)) : list);
      })
      .catch((e) => !cancelled && setError(errorMessage(e)))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [q, storeId, sort, selectedCategory]);

  const setParam = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    if (value && !(key === 'category' && value === 'all') && !(key === 'sort' && value === 'newest')) next.set(key, value);
    else next.delete(key);
    setParams(next, { replace: true });
  };

  return (
    <>
      <div className="shop-grid__top-space">
        <div className="shop-grid__header">
          <img src="/images/shop_item.png" alt="Shop" className="shop-grid__icon" />
        </div>

        <div className="shop-grid__filters">
          {FILTERS.map((category) => (
            <button
              key={category}
              className={`shop-grid__filter-btn ${selectedCategory === category ? 'shop-grid__filter-btn--active' : ''}`}
              onClick={() => setParam('category', category)}
              title={t.product.categoryDescriptions[category]}
            >
              <img
                src={`/images/${t.product.categories[category]}`}
                alt={category}
                style={{ width: '40px', height: '40px', objectFit: 'contain' }}
              />
              {selectedCategory === category && (
                <span className="shop-grid__filter-text">{t.product.categoryDescriptions[category]}</span>
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="shop-grid">
        {banner}
        <div className="fw-toolbar">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              setParam('q', keyword.trim());
            }}
          >
            <input
              className="fw-input"
              type="search"
              placeholder={t.shop.searchPlaceholder}
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
            />
            <button className="fw-btn" type="submit">
              🔍 {t.shop.search}
            </button>
          </form>
          <select className="fw-select" value={storeId} onChange={(e) => setParam('store', e.target.value)}>
            <option value="">{t.shop.allStores}</option>
            {stores.map((s) => (
              <option key={s.store_id} value={s.store_id}>
                {s.name}
              </option>
            ))}
          </select>
          <select className="fw-select" value={sort} onChange={(e) => setParam('sort', e.target.value)}>
            <option value="newest">{t.shop.sortNewest}</option>
            <option value="price_asc">{t.shop.sortPriceAsc}</option>
            <option value="price_desc">{t.shop.sortPriceDesc}</option>
          </select>
          {!loading && !error && (
            <span className="fw-muted">
              {products.length} {t.shop.resultCount}
            </span>
          )}
        </div>

        {error && <div className="fw-error">{t.shop.loadFailed}：{error}</div>}

        <div className="shop-grid__products">
          {loading ? (
            <div className="shop-grid__empty">
              <p>{t.product.loading}</p>
            </div>
          ) : products.length > 0 ? (
            products.map((product) => <ProductCard key={product.product_id} product={product} onClick={onProductClick} />)
          ) : (
            <div className="shop-grid__empty">
              <p>{t.product.categoryDescriptions[selectedCategory] ?? ''}</p>
              <p>{t.shop.empty}</p>
            </div>
          )}
        </div>
      </div>

      <div className="shop-grid__footer"></div>
    </>
  );
};
