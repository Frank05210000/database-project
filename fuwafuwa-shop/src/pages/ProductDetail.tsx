import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import { ReactionPreview } from '../components/Pet/ReactionPreview';
import { useLanguage } from '../i18n';
import { useAuth } from '../contexts/AuthContext';
import { useCart } from '../hooks';
import { ApiError, errorMessage, formatMoney } from '../api/client';
import type { Product } from '../api/types';
import { getProduct } from '../services/productService';
import { readFavorites, toggleFavorite } from '../utils/favorites';
import { eventBadge, imageFallback, productImage, reactionFor } from '../utils/product';
import './ProductDetail.css';

export const ProductDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { t, language } = useLanguage();
  const { user, hasRole } = useAuth();
  const { addToCart } = useCart();

  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [adding, setAdding] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [isFavorited, setIsFavorited] = useState(false);

  useEffect(() => {
    const pid = Number(id);
    if (!Number.isInteger(pid)) {
      setLoading(false);
      setLoadError(t.product.notFound);
      return;
    }
    setLoading(true);
    setLoadError(null);
    setMessage(null);
    setQuantity(1);
    getProduct(pid)
      .then((p) => {
        setProduct(p);
        setIsFavorited(readFavorites().includes(p.product_id));
      })
      .catch((e) => {
        setProduct(null);
        setLoadError(e instanceof ApiError && e.status === 404 ? t.product.notFound : errorMessage(e));
      })
      .finally(() => setLoading(false));
    window.scrollTo(0, 0);
  }, [id]);

  if (loading) {
    return (
      <div className="product-detail">
        <div className="product-detail__loading">{t.product.loading}</div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="product-detail">
        <button className="product-detail__back-btn" onClick={() => navigate('/')}>
          {t.product.back}
        </button>
        <div className="fw-error" style={{ margin: 24 }}>{loadError ?? t.product.notFound}</div>
      </div>
    );
  }

  const maxQty = Math.max(product.stock, 0);
  const badge = eventBadge(product.event_discount, language);
  const setQty = (n: number) => setQuantity(Math.max(1, Math.min(maxQty || 1, Math.floor(n) || 1)));

  const handleAddToCart = async () => {
    if (!user) {
      navigate('/login', { state: { from: location.pathname } });
      return;
    }
    if (!hasRole('customer')) {
      setMessage({ ok: false, text: t.cart.customerOnly });
      return;
    }
    setAdding(true);
    setMessage(null);
    try {
      await addToCart(product.product_id, quantity);
      setMessage({ ok: true, text: `${product.name} × ${quantity} ${t.messages.addedToCart}` });
    } catch (e) {
      setMessage({ ok: false, text: errorMessage(e) || t.messages.addToCartFailed });
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="product-detail">
      <button className="product-detail__back-btn" onClick={() => navigate(-1)}>
        {t.product.back}
      </button>

      <div className="product-detail__carousel">
        <div className="product-detail__image-container">
          <img
            src={productImage(product)}
            alt={product.name}
            className="product-detail__image"
            onError={imageFallback(product.category)}
          />
        </div>
      </div>

      <div className="product-detail__info">
        <div className="product-detail__header">
          <h1 className="product-detail__title">{product.name}</h1>
          <span className="product-detail__category-badge">
            {t.product.categoryDescriptions[product.category as keyof typeof t.product.categoryDescriptions] ??
              product.category}
          </span>
        </div>
        <p className="product-detail__price">{formatMoney(product.price)}</p>
        {product.event_discount && (
          <p style={{ marginTop: 6 }}>
            <span className="fw-event-badge">{badge}</span>{' '}
            <span>
              {t.product.eventDiscount}：{product.event_discount.description}（{product.event_discount.start_date} ~{' '}
              {product.event_discount.end_date}）
            </span>
          </p>
        )}
        <p style={{ marginTop: 6 }}>
          {t.product.store}：<Link to={`/stores/${product.store_id}`}>{product.store_name}</Link>
        </p>
      </div>

      <div className="product-detail__description">
        <h2 className="product-detail__section-title">{t.product.description}</h2>
        <p>{product.description}</p>
        <div className="product-detail__stock">
          {t.product.stock}: {product.stock > 0 ? `${product.stock}${t.product.pieces}` : t.product.outOfStock}
        </div>
        {product.stock > 0 && (
          <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <span>{t.product.quantity}</span>
            <div className="fw-qty">
              <button type="button" onClick={() => setQty(quantity - 1)} disabled={quantity <= 1}>
                −
              </button>
              <input
                type="number"
                min={1}
                max={maxQty}
                value={quantity}
                onChange={(e) => setQty(Number(e.target.value))}
              />
              <button type="button" onClick={() => setQty(quantity + 1)} disabled={quantity >= maxQty}>
                +
              </button>
            </div>
            <button className="fw-btn" onClick={handleAddToCart} disabled={adding}>
              🛒 {t.product.addToCart}
            </button>
          </div>
        )}
        {message && <div className={message.ok ? 'fw-success' : 'fw-error'}>{message.text}</div>}
      </div>

      {product.also_bought && product.also_bought.length > 0 && (
        <div className="product-detail__description">
          <h2 className="product-detail__section-title">{t.product.alsoBought}</h2>
          <div className="fw-also-bought">
            {product.also_bought.map((p) => (
              <div key={p.product_id} className="fw-mini-card" onClick={() => navigate(`/product/${p.product_id}`)}>
                <img src={productImage(p)} alt={p.name} onError={imageFallback(p.category)} />
                <div>{p.name}</div>
                <div style={{ color: 'var(--color-accent-red)', fontWeight: 700 }}>{formatMoney(p.price)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="product-detail__reaction">
        <ReactionPreview reactionType={reactionFor(product.category)} />
      </div>

      <div className="product-detail__footer">
        <button
          className="product-detail__buy-btn"
          onClick={handleAddToCart}
          disabled={product.stock === 0 || adding}
          title={t.product.addToCart}
        >
          <img src="/images/buy_button.webp" alt={t.product.addToCart} />
        </button>
        <button
          className="product-detail__dog-heart"
          onClick={() => setIsFavorited(toggleFavorite(product.product_id))}
          aria-label="Add to favorites"
        >
          <img src={isFavorited ? '/images/dog_heart_press_2.webp' : '/images/dog_heart_press_1.webp'} alt="heart" />
        </button>
      </div>
    </div>
  );
};
