import React from 'react';
import type { Product } from '../../api/types';
import { formatMoney } from '../../api/client';
import { useLanguage } from '../../i18n';
import { categoryImage, eventBadge, imageFallback, productImage } from '../../utils/product';
import './ProductCard.css';

interface ProductCardProps {
  product: Product;
  onClick?: (product: Product) => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({ product, onClick }) => {
  const { language, t } = useLanguage();
  const badge = eventBadge(product.event_discount, language);

  return (
    <div className="product-card" onClick={() => onClick?.(product)}>
      <div className="product-card__image-container">
        {badge && (
          <span className="fw-event-badge product-card__event" title={product.event_discount?.description}>
            {badge}
          </span>
        )}
        <img
          src={productImage(product)}
          alt={product.name}
          className="product-card__image"
          onError={imageFallback(product.category)}
        />
      </div>

      <div className="product-card__content">
        <h3 className="product-card__name">{product.name}</h3>
        <div className="product-card__store">{product.store_name}</div>
        <div className="product-card__footer">
          <span className="product-card__price">{formatMoney(product.price)}</span>
          <div className="product-card__category-badge">
            <img
              src={categoryImage(product.category)}
              alt={product.category ?? ''}
              style={{ width: '100%', height: '100%', objectFit: 'contain' }}
            />
          </div>
        </div>
        {product.stock === 0 && <div className="product-card__soldout">{t.product.outOfStock}</div>}
      </div>
    </div>
  );
};
