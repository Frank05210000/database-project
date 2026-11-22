import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ApiError, errorMessage, formatDateTime } from '../api/client';
import type { Store } from '../api/types';
import { getStore } from '../services/storeService';
import { useLanguage } from '../i18n';
import { Stars } from '../components/Common/Stars';
import { ProductCard } from '../components/Shop/ProductCard';
import '../components/Shop/ShopGrid.css';

/** STS：商店資訊、商品與顧客評價 */
const StoreDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [store, setStore] = useState<Store | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getStore(Number(id))
      .then(setStore)
      .catch((e) => setError(e instanceof ApiError && e.status === 404 ? '找不到這間商店' : errorMessage(e)))
      .finally(() => setLoading(false));
  }, [id]);

  return (
    <div className="store-page">
      <button className="fw-btn fw-btn--ghost" onClick={() => navigate('/stores')} style={{ marginBottom: 16 }}>
        ← {t.store.title}
      </button>
      {loading && <p>{t.product.loading}</p>}
      {error && <div className="fw-error">{error}</div>}
      {store && (
        <>
          <div className="fw-panel">
            <h1 style={{ marginBottom: 8 }}>🏪 {store.name}</h1>
            <div style={{ marginBottom: 8 }}>
              <Stars value={store.avg_rating} />{' '}
              <strong>{store.avg_rating != null ? Number(store.avg_rating).toFixed(1) : '—'}</strong>{' '}
              <span className="fw-muted">
                {t.store.avgRating}・{store.review_count} {t.store.reviewCount}・{store.product_count}{' '}
                {t.store.productCount}
              </span>
            </div>
            <div>📍 {t.store.address}：{store.address}</div>
            <div>☎ {t.store.phone}：{store.phone}</div>
            <div>✉ {t.store.email}：{store.email}</div>
          </div>

          <div className="fw-panel">
            <h2>{t.store.products}</h2>
            <div className="shop-grid__products">
              {(store.products ?? []).length === 0 && <p>{t.shop.empty}</p>}
              {(store.products ?? []).map((p) => (
                <ProductCard key={p.product_id} product={p} onClick={() => navigate(`/product/${p.product_id}`)} />
              ))}
            </div>
          </div>

          <div className="fw-panel">
            <h2>{t.store.reviews}</h2>
            {(store.reviews ?? []).length === 0 ? (
              <p className="fw-muted">{t.store.noReviews}</p>
            ) : (
              <ul className="store-reviews">
                {(store.reviews ?? []).map((r) => (
                  <li key={r.order_id}>
                    <div>
                      <Stars value={r.rating} /> <strong>{r.customer_name}</strong>{' '}
                      <span className="fw-muted">{formatDateTime(r.reviewed_at)}</span>
                    </div>
                    {r.comment && <div>{r.comment}</div>}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default StoreDetailPage;
