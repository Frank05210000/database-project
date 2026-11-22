import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BasketVisualizer } from '../components/Cart/BasketVisualizer';
import { AmountBreakdown, amountsFromQuote } from '../components/Cart/AmountBreakdown';
import { useLanguage } from '../i18n';
import { useCart } from '../hooks';
import { useAuth } from '../contexts/AuthContext';
import { errorMessage, formatMoney } from '../api/client';
import { imageFallback, productImage } from '../utils/product';
import './CartPage.css';

export const CartPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const { user, loading: authLoading } = useAuth();
  const { cart, enabled, loading, updateQuantity, removeItem } = useCart();
  const [lineErrors, setLineErrors] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState<number | null>(null);

  const run = async (productId: number, fn: () => Promise<void>) => {
    setBusy(productId);
    setLineErrors((e) => ({ ...e, [productId]: '' }));
    try {
      await fn();
    } catch (err) {
      // 例如 409 BR-06：數量超過庫存
      setLineErrors((e) => ({ ...e, [productId]: errorMessage(err) }));
    } finally {
      setBusy(null);
    }
  };

  const header = (
    <div className="cart-page__header">
      <button className="cart-page__back-btn" onClick={() => navigate('/')}>
        {t.product.back}
      </button>
      <h1 className="cart-page__title">{t.cart.title}</h1>
    </div>
  );

  if (!authLoading && (!user || !enabled)) {
    return (
      <div className="cart-page">
        {header}
        <div className="cart-page__items">
          <div className="cart-page__empty">
            <p>{user ? t.cart.customerOnly : t.cart.loginFirst}</p>
            {!user && (
              <button className="fw-btn" onClick={() => navigate('/login', { state: { from: '/cart' } })}>
                {t.nav.login}
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  const items = cart?.items ?? [];
  const lineInfo = new Map((cart?.quote.lines ?? []).map((l) => [l.product_id, l]));

  return (
    <div className="cart-page">
      {header}

      <div className="cart-page__items">
        {items.length === 0 ? (
          <div className="cart-page__empty">
            <p>{loading ? t.product.loading : t.cart.empty}</p>
            <img src="/images/dog.png" alt="Empty" className="cart-page__empty-icon" />
            <div>
              <button className="fw-btn" onClick={() => navigate('/')}>
                {t.cart.continueShopping}
              </button>
            </div>
          </div>
        ) : (
          <>
            {items.map((item) => {
              const p = item.product;
              const line = lineInfo.get(p.product_id);
              return (
                <React.Fragment key={p.product_id}>
                  <div className="cart-page__item">
                    <img
                      src={productImage(p)}
                      alt={p.name}
                      className="cart-page__item-image"
                      onError={imageFallback(p.category)}
                      onClick={() => navigate(`/product/${p.product_id}`)}
                      style={{ cursor: 'pointer' }}
                    />
                    <div className="cart-page__item-info">
                      <h3 className="cart-page__item-name">{p.name}</h3>
                      <p className="cart-page__item-price">{formatMoney(p.price)}</p>
                      <p className="fw-muted">
                        {p.store_name}・{t.product.stock} {p.stock}
                      </p>
                      {line && line.event_discount > 0 && (
                        <p style={{ fontSize: 13 }}>
                          <span className="fw-event-badge">{line.event_code}</span> {line.event_description}{' '}
                          <strong style={{ color: '#2e7d32' }}>− {formatMoney(line.event_discount)}</strong>
                        </p>
                      )}
                    </div>
                    <div className="cart-page__item-controls">
                      <div className="cart-page__item-total">{formatMoney(item.line_subtotal)}</div>
                      <div className="cart-page__item-quantity">
                        <button
                          onClick={() => run(p.product_id, () => updateQuantity(p.product_id, item.quantity - 1))}
                          disabled={item.quantity <= 1 || busy === p.product_id}
                        >
                          -
                        </button>
                        <span>{item.quantity}</span>
                        <button
                          onClick={() => run(p.product_id, () => updateQuantity(p.product_id, item.quantity + 1))}
                          disabled={busy === p.product_id}
                        >
                          +
                        </button>
                      </div>
                      <button
                        className="cart-page__item-remove"
                        onClick={() => run(p.product_id, () => removeItem(p.product_id))}
                        disabled={busy === p.product_id}
                      >
                        {t.cart.remove}
                      </button>
                    </div>
                  </div>
                  {lineErrors[p.product_id] && <div className="fw-error">{lineErrors[p.product_id]}</div>}
                </React.Fragment>
              );
            })}

            {cart && (
              <div className="cart-page__summary">
                <AmountBreakdown amounts={amountsFromQuote(cart.quote)} taxRate={cart.quote.tax_rate} />
              </div>
            )}

            <button className="cart-page__checkout-btn" onClick={() => navigate('/order')} title={t.cart.checkout}>
              <img src="/images/checkout.png" alt={t.cart.checkout} />
            </button>
          </>
        )}
      </div>

      {items.length > 0 && <BasketVisualizer cartItems={items} />}
    </div>
  );
};
