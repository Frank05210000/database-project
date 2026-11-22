import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../i18n';
import {
  errorMessage,
  formatDateTime,
  formatMoney,
  ORDER_STATUS_LABEL,
  RETURN_STATUS_LABEL,
} from '../api/client';
import type { Order, Store } from '../api/types';
import { cancelOrder, createReturn, getOrder } from '../services/orderService';
import { listStores, reviewStore } from '../services/storeService';
import { AmountBreakdown, amountsFromOrder } from '../components/Cart/AmountBreakdown';
import { imageFallback } from '../utils/product';
import './OrderDetailPage.css';

const STEPS = [
  { status: 'received', icon: '📝' },
  { status: 'processing', icon: '📦' },
  { status: 'shipping', icon: '🚚' },
  { status: 'closed', icon: '✅' },
];

/** 退貨申請表單（OMS-F-012）：選擇品項與數量（不超過購買數量）並填寫原因 */
const ReturnForm: React.FC<{ order: Order; onDone: () => void }> = ({ order, onDone }) => {
  const [qty, setQty] = useState<Record<number, number>>({});
  const [reason, setReason] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const items = Object.entries(qty)
      .filter(([, n]) => n > 0)
      .map(([itemNo, n]) => ({ item_no: Number(itemNo), return_qty: n }));
    if (items.length === 0) {
      setError('請至少選擇一項要退貨的商品');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await createReturn({ order_id: order.order_id, reason: reason.trim(), items });
      onDone();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={submit}>
      <table className="fw-table">
        <thead>
          <tr>
            <th>商品</th>
            <th>單價</th>
            <th>購買數量</th>
            <th>退貨數量</th>
          </tr>
        </thead>
        <tbody>
          {order.items.map((it) => (
            <tr key={it.item_no}>
              <td>{it.product_name}</td>
              <td>{formatMoney(it.unit_price)}</td>
              <td>{it.quantity}</td>
              <td>
                <input
                  className="fw-input"
                  type="number"
                  min={0}
                  max={it.quantity}
                  style={{ width: 80 }}
                  value={qty[it.item_no] ?? 0}
                  onChange={(e) =>
                    setQty({
                      ...qty,
                      [it.item_no]: Math.max(0, Math.min(it.quantity, Math.floor(Number(e.target.value)) || 0)),
                    })
                  }
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <label style={{ display: 'block', marginTop: 12, fontWeight: 600 }}>
        退貨原因 *
        <textarea
          className="fw-textarea"
          rows={3}
          required
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="請說明退貨原因"
        />
      </label>
      {error && <div className="fw-error">{error}</div>}
      <button className="fw-btn" type="submit" disabled={submitting} style={{ marginTop: 8 }}>
        {submitting ? '送出中...' : '送出退貨申請'}
      </button>
    </form>
  );
};

/** 已完成訂單可以評價購買過的商店 */
const ReviewForm: React.FC<{ order: Order; stores: Store[] }> = ({ order, stores }) => {
  const names = Array.from(new Set(order.items.map((i) => i.store_name)));
  const candidates = stores.filter((s) => names.includes(s.name));
  const [storeId, setStoreId] = useState<number | ''>(candidates[0]?.store_id ?? '');
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (candidates.length === 0) return null;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (storeId === '') return;
    setSubmitting(true);
    setMsg(null);
    try {
      await reviewStore(storeId, { order_id: order.order_id, rating, comment: comment.trim() || undefined });
      setMsg({ ok: true, text: '感謝您的評價！' });
      setComment('');
    } catch (err) {
      setMsg({ ok: false, text: errorMessage(err) });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={submit} className="fw-form-grid">
      <label>
        商店
        <select className="fw-select" value={storeId} onChange={(e) => setStoreId(Number(e.target.value))}>
          {candidates.map((s) => (
            <option key={s.store_id} value={s.store_id}>
              {s.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        評分
        <select className="fw-select" value={rating} onChange={(e) => setRating(Number(e.target.value))}>
          {[5, 4, 3, 2, 1].map((n) => (
            <option key={n} value={n}>
              {'★'.repeat(n)} {n}
            </option>
          ))}
        </select>
      </label>
      <label style={{ gridColumn: '1 / -1' }}>
        評論（選填）
        <textarea className="fw-textarea" rows={2} value={comment} onChange={(e) => setComment(e.target.value)} />
      </label>
      <div style={{ gridColumn: '1 / -1' }}>
        {msg && <div className={msg.ok ? 'fw-success' : 'fw-error'}>{msg.text}</div>}
        <button className="fw-btn" type="submit" disabled={submitting}>
          送出評價
        </button>
      </div>
    </form>
  );
};

const OrderDetailPage: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const navigate = useNavigate();
  const { t } = useLanguage();
  const { user, loading: authLoading } = useAuth();
  const [order, setOrder] = useState<Order | null>(null);
  const [stores, setStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [showReturn, setShowReturn] = useState(false);
  const [cancelling, setCancelling] = useState(false);

  const load = useCallback(async () => {
    try {
      setOrder(await getOrder(Number(orderId)));
      setError(null);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setLoading(false);
      return;
    }
    load();
  }, [authLoading, user, load]);

  useEffect(() => {
    if (order?.status === 'closed') listStores().then(setStores).catch(() => setStores([]));
  }, [order?.status]);

  const handleCancel = async () => {
    if (!order || !window.confirm('確定要取消此訂單嗎？')) return;
    setCancelling(true);
    setActionError(null);
    try {
      setOrder(await cancelOrder(order.order_id));
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setCancelling(false);
    }
  };

  if (!authLoading && !user) {
    return (
      <div className="order-detail-page">
        <div className="detail-container">
          <h2>請先登入</h2>
          <button onClick={() => navigate('/login', { state: { from: `/order/${orderId}` } })}>前往登入</button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="order-detail-page">
        <div className="loading">{t.product.loading}</div>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="order-detail-page">
        <div className="detail-container">
          <div className="error-message">{error || '訂單不存在'}</div>
          <button onClick={() => navigate('/my-orders')}>{t.orders.back}</button>
        </div>
      </div>
    );
  }

  const stepIndex = STEPS.findIndex((s) => s.status === order.status);
  const ret = order.return_request;

  return (
    <div className="order-detail-page">
      <div className="detail-container">
        <div className="detail-header">
          <button className="back-button" onClick={() => navigate('/my-orders')}>
            {t.orders.back}
          </button>
          <h1>訂單詳情</h1>
        </div>

        <div className="order-status-card">
          <div className="status-header">
            <div className="order-number">
              <span className="label">{t.orders.orderNo}</span>
              <span className="value">#{order.order_id}</span>
            </div>
            <div className={`order-status status-${order.status}`}>
              {ORDER_STATUS_LABEL[order.status] ?? order.status}
            </div>
          </div>
          <div className="order-date">
            {t.orders.orderTime}：{formatDateTime(order.order_time)}・付款時間：{formatDateTime(order.paid_at)}
          </div>
          {(order.can_cancel || order.can_return) && (
            <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {order.can_cancel && (
                <button className="fw-btn fw-btn--danger" onClick={handleCancel} disabled={cancelling}>
                  {cancelling ? '取消中...' : '取消訂單'}
                </button>
              )}
              {order.can_return && !showReturn && (
                <button className="fw-btn" onClick={() => setShowReturn(true)}>
                  申請退貨
                </button>
              )}
            </div>
          )}
          {actionError && <div className="fw-error">{actionError}</div>}
        </div>

        <div className="order-progress">
          <h2>訂單進度</h2>
          {stepIndex >= 0 ? (
            <div className="progress-steps">
              {STEPS.map((s, i) => (
                <div key={s.status} className={`step ${i <= stepIndex ? 'active' : ''}`}>
                  <div className="step-icon">{s.icon}</div>
                  <div className="step-text">{ORDER_STATUS_LABEL[s.status]}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="cancelled-notice">
              {order.status === 'cancelled' ? '❌ 此訂單已取消' : `↩️ 此訂單${ORDER_STATUS_LABEL[order.status]}`}
            </div>
          )}
          <h3 style={{ margin: '16px 0 8px' }}>狀態歷程</h3>
          <ul className="fw-timeline">
            {order.history.map((h) => (
              <li key={h.seq_no}>
                <span className="fw-timeline__status">{ORDER_STATUS_LABEL[h.status] ?? h.status}</span>{' '}
                <span className="fw-muted">
                  {formatDateTime(h.changed_at)}・{h.changed_by_name}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {showReturn && order.can_return && (
          <div className="fw-panel">
            <h2>申請退貨</h2>
            <ReturnForm
              order={order}
              onDone={() => {
                setShowReturn(false);
                load();
              }}
            />
            <button className="fw-btn fw-btn--ghost" style={{ marginTop: 8 }} onClick={() => setShowReturn(false)}>
              取消
            </button>
          </div>
        )}

        {ret && (
          <div className="fw-panel">
            <h2>
              退貨申請 #{ret.return_id}{' '}
              <span className="fw-return-tag">{RETURN_STATUS_LABEL[ret.status] ?? ret.status}</span>
            </h2>
            <p>申請時間：{formatDateTime(ret.requested_at)}</p>
            <p>退貨原因：{ret.reason}</p>
            <table className="fw-table" style={{ margin: '8px 0' }}>
              <thead>
                <tr>
                  <th>商品</th>
                  <th>單價</th>
                  <th>購買</th>
                  <th>退貨</th>
                  <th>退款</th>
                </tr>
              </thead>
              <tbody>
                {ret.items.map((it) => (
                  <tr key={it.item_no}>
                    <td>{it.product_name}</td>
                    <td>{formatMoney(it.unit_price)}</td>
                    <td>{it.quantity}</td>
                    <td>{it.return_qty}</td>
                    <td>{it.refund_amount != null ? formatMoney(it.refund_amount) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {ret.status === 'approved' && (
              <div className="fw-success">
                已核准，退款金額 {formatMoney(ret.refund_total)}（{ret.processed_by_name}・
                {formatDateTime(ret.processed_at)}）
              </div>
            )}
            {ret.status === 'rejected' && (
              <div className="fw-error">
                已拒絕：{ret.reject_reason}（{ret.processed_by_name}・{formatDateTime(ret.processed_at)}）
              </div>
            )}
            {ret.status === 'pending' && <div className="fw-muted">工作人員審核中，請耐心等候。</div>}
          </div>
        )}

        <div className="order-items-section">
          <h2>{t.checkout.items}</h2>
          <div className="items-list">
            {order.items.map((item) => (
              <div key={item.item_no} className="item-row">
                <img
                  src={item.image_url ?? '/images/All.webp'}
                  alt={item.product_name}
                  className="item-image"
                  onError={imageFallback(null)}
                  onClick={() => navigate(`/product/${item.product_id}`)}
                  style={{ cursor: 'pointer' }}
                />
                <div className="item-info">
                  <h3>{item.product_name}</h3>
                  <p className="item-description">
                    {item.store_name}
                    {item.event_discount > 0 && (
                      <span style={{ color: '#2e7d32' }}>・活動折扣 − {formatMoney(item.event_discount)}</span>
                    )}
                  </p>
                </div>
                <div className="item-price">
                  <div className="unit-price">{formatMoney(item.unit_price)}</div>
                  <div className="quantity">x {item.quantity}</div>
                </div>
                <div className="item-subtotal">{formatMoney(item.line_subtotal)}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="shipping-info-section">
          <h2>配送資訊</h2>
          <div className="info-grid">
            <div className="info-row">
              <span className="info-label">收件人：</span>
              <span className="info-value">{order.recipient_name}</span>
            </div>
            <div className="info-row">
              <span className="info-label">聯絡電話：</span>
              <span className="info-value">{order.recipient_phone}</span>
            </div>
            <div className="info-row">
              <span className="info-label">配送地址：</span>
              <span className="info-value">{order.recipient_address}</span>
            </div>
          </div>
        </div>

        <div className="payment-info-section">
          <h2>金額明細</h2>
          <AmountBreakdown amounts={amountsFromOrder(order)} />
        </div>

        {order.status === 'closed' && stores.length > 0 && (
          <div className="fw-panel">
            <h2>評價商店</h2>
            <ReviewForm order={order} stores={stores} />
          </div>
        )}

        <div className="action-buttons">
          <button className="btn-secondary" onClick={() => navigate('/my-orders')}>
            返回訂單列表
          </button>
          <button className="btn-primary" onClick={() => navigate('/')}>
            {t.cart.continueShopping}
          </button>
        </div>
      </div>
    </div>
  );
};

export default OrderDetailPage;
