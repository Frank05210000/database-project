import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useCart } from '../hooks';
import { useLanguage } from '../i18n';
import { errorMessage, formatMoney } from '../api/client';
import type { CheckoutPreview } from '../api/types';
import { createOrder, getCheckoutPreview } from '../services/orderService';
import { AmountBreakdown, amountsFromQuote } from '../components/Cart/AmountBreakdown';
import './OrderPage.css';

/** 結帳（OMS-F-001/002）：預覽金額、填寫收件資訊（預設帶入會員資料）、確認付款 */
const OrderPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const { user, loading: authLoading } = useAuth();
  const { reset, refresh } = useCart();
  const [preview, setPreview] = useState<CheckoutPreview | null>(null);
  const [recipient, setRecipient] = useState({ name: '', phone: '', address: '' });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      navigate('/login', { replace: true, state: { from: '/order' } });
      return;
    }
    getCheckoutPreview()
      .then((p) => {
        setPreview(p);
        setRecipient({
          name: p.recipient.name ?? '',
          phone: p.recipient.phone ?? '',
          address: p.recipient.address ?? '',
        });
      })
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false));
  }, [authLoading, user, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const order = await createOrder({
        recipient_name: recipient.name.trim(),
        recipient_phone: recipient.phone.trim(),
        recipient_address: recipient.address.trim(),
      });
      reset();
      refresh();
      navigate(`/order-success/${order.order_id}`, { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="order-page">
        <div className="order-container">
          <p>{t.product.loading}</p>
        </div>
      </div>
    );
  }

  const quote = preview?.quote;
  if (!quote || quote.lines.length === 0) {
    return (
      <div className="order-page">
        <div className="order-container">
          <h2>{t.checkout.emptyCart}</h2>
          {error && <div className="error-message">{error}</div>}
          <button className="btn-primary" onClick={() => navigate('/')}>
            {t.cart.continueShopping}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="order-page">
      <div className="order-container">
        <h1>{t.checkout.title}</h1>

        <form onSubmit={handleSubmit}>
          <section className="order-section">
            <h2>{t.checkout.items}</h2>
            <table className="fw-table">
              <thead>
                <tr>
                  <th>商品</th>
                  <th>單價</th>
                  <th>數量</th>
                  <th>小計</th>
                  <th>活動折扣</th>
                  <th>折後</th>
                </tr>
              </thead>
              <tbody>
                {quote.lines.map((l) => (
                  <tr key={l.product_id}>
                    <td>
                      {l.product_name}
                      {l.event_code && (
                        <div className="fw-muted">
                          <span className="fw-event-badge">{l.event_code}</span> {l.event_description}
                        </div>
                      )}
                    </td>
                    <td>{formatMoney(l.unit_price)}</td>
                    <td>{l.quantity}</td>
                    <td>{formatMoney(l.line_subtotal)}</td>
                    <td>{l.event_discount > 0 ? `− ${formatMoney(l.event_discount)}` : '—'}</td>
                    <td>{formatMoney(l.net_amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="order-section">
            <h2>{t.checkout.recipient}</h2>
            <div className="address-form">
              <div className="form-row">
                <div className="form-group">
                  <label>{t.checkout.recipientName} *</label>
                  <input
                    type="text"
                    required
                    value={recipient.name}
                    onChange={(e) => setRecipient({ ...recipient, name: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>{t.checkout.recipientPhone} *</label>
                  <input
                    type="tel"
                    required
                    value={recipient.phone}
                    onChange={(e) => setRecipient({ ...recipient, phone: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label>{t.checkout.recipientAddress} *</label>
                <input
                  type="text"
                  required
                  value={recipient.address}
                  onChange={(e) => setRecipient({ ...recipient, address: e.target.value })}
                />
              </div>
            </div>
          </section>

          <section className="order-section order-summary">
            <h2>{t.checkout.summary}</h2>
            <AmountBreakdown amounts={amountsFromQuote(quote)} taxRate={quote.tax_rate} />
          </section>

          {error && <div className="error-message">{error}</div>}

          <div className="order-actions">
            <button type="button" className="btn-secondary" onClick={() => navigate('/cart')} disabled={submitting}>
              {t.checkout.backToCart}
            </button>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? t.checkout.paying : `${t.checkout.pay}（${formatMoney(quote.total)}）`}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default OrderPage;
