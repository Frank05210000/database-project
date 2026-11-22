import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { errorMessage } from '../api/client';
import type { Store } from '../api/types';
import { listStores } from '../services/storeService';
import { useLanguage } from '../i18n';
import { Stars } from '../components/Common/Stars';

/** STS：商店一覽 */
const StoresPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [stores, setStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listStores()
      .then(setStores)
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="store-page">
      <h1>🏪 {t.store.title}</h1>
      {loading && <p>{t.product.loading}</p>}
      {error && <div className="fw-error">{error}</div>}
      <div className="store-list">
        {stores.map((s) => (
          <div key={s.store_id} className="store-card" onClick={() => navigate(`/stores/${s.store_id}`)}>
            <h3>{s.name}</h3>
            <div>
              <Stars value={s.avg_rating} />{' '}
              <span className="fw-muted">
                {s.avg_rating != null ? Number(s.avg_rating).toFixed(1) : '—'}（{s.review_count} {t.store.reviewCount}）
              </span>
            </div>
            <div className="fw-muted">📍 {s.address}</div>
            <div className="fw-muted">☎ {s.phone}</div>
            <div className="fw-muted">
              {s.product_count} {t.store.productCount}
            </div>
            <div style={{ marginTop: 'auto' }}>
              <button className="fw-btn fw-btn--ghost">{t.store.viewStore} →</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StoresPage;
