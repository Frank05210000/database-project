import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SplitScreen } from '../components/Layout/SplitScreen';
import { PetRoom } from '../components/Pet/PetRoom';
import { ShopGrid } from '../components/Shop/ShopGrid';
import { DISCOUNT_TYPE_LABEL } from '../api/client';
import type { Discount, Product } from '../api/types';
import { getActiveDiscounts } from '../services/discountService';
import { useLanguage } from '../i18n';
import './HomePage.css';

/** 首頁上方顯示今天有效的折扣（端點尚未完成時不顯示） */
const DiscountBanner: React.FC<{ discounts: Discount[] }> = ({ discounts }) => {
  const { t } = useLanguage();
  if (discounts.length === 0) return null;
  return (
    <div className="fw-discount-banner">
      <span className="fw-discount-banner__title">🎉 {t.home.activeDiscounts}</span>
      {discounts.map((d) => (
        <span key={d.discount_code} className="fw-discount-chip" title={`${d.start_date} ~ ${d.end_date}`}>
          {DISCOUNT_TYPE_LABEL[d.discount_type] ?? d.discount_type}｜{d.description}
        </span>
      ))}
    </div>
  );
};

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [discounts, setDiscounts] = useState<Discount[]>([]);

  useEffect(() => {
    getActiveDiscounts().then(setDiscounts);
  }, []);

  return (
    <div className="home-page">
      <SplitScreen
        topSection={<PetRoom />}
        bottomSection={
          <ShopGrid
            banner={<DiscountBanner discounts={discounts} />}
            onProductClick={(p: Product) => navigate(`/product/${p.product_id}`)}
          />
        }
        topHeight="40%"
      />
      <div className="home-page__footer"></div>
    </div>
  );
};
