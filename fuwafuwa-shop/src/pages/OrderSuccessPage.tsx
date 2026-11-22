import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { errorMessage, formatDateTime, formatMoney, ORDER_STATUS_LABEL } from '../api/client';
import type { Order } from '../api/types';
import { getOrder } from '../services/orderService';
import { imageFallback } from '../utils/product';
import { useLanguage } from '../i18n';
import './OrderSuccessPage.css';

const OrderSuccessPage: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getOrder(Number(orderId))
      .then(setOrder)
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false));
  }, [orderId]);

  if (loading) {
    return (
      <div className="order-success-page">
        <div className="loading">{t.product.loading}</div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="order-success-page">
        <div className="error-container">
          <h2>找不到訂單</h2>
          {error && <p>{error}</p>}
          <button onClick={() => navigate('/')}>返回首頁</button>
        </div>
      </div>
    );
  }

  return (
    <div className="order-success-page">
      <div className="success-container">
        <div className="success-icon">✓</div>
        <h1>付款成功，訂單已成立！</h1>
        <p className="success-message">{t.messages.thankYou}我們將盡快為您處理訂單</p>

        <div className="order-info">
          <div className="info-row">
            <span className="label">{t.orders.orderNo}：</span>
            <span className="value">#{order.order_id}</span>
          </div>
          <div className="info-row">
            <span className="label">訂單狀態：</span>
            <span className="value">{ORDER_STATUS_LABEL[order.status] ?? order.status}</span>
          </div>
          <div className="info-row">
            <span className="label">付款時間：</span>
            <span className="value">{formatDateTime(order.paid_at)}</span>
          </div>
          <div className="info-row">
            <span className="label">{t.orders.total}：</span>
            <span className="value amount">{formatMoney(order.total)}</span>
          </div>
        </div>

        <div className="order-items">
          <h2>{t.checkout.items}</h2>
          {order.items.map((item) => (
            <div key={item.item_no} className="item-row">
              <img src={item.image_url ?? '/images/All.webp'} alt={item.product_name} onError={imageFallback(null)} />
              <div className="item-info">
                <h3>{item.product_name}</h3>
                <p>
                  {formatMoney(item.unit_price)} × {item.quantity}
                </p>
              </div>
              <div className="item-price">{formatMoney(item.line_subtotal)}</div>
            </div>
          ))}
        </div>

        <div className="shipping-info">
          <h2>配送資訊</h2>
          <p>
            <strong>收件人：</strong>
            {order.recipient_name}
          </p>
          <p>
            <strong>電話：</strong>
            {order.recipient_phone}
          </p>
          <p>
            <strong>地址：</strong>
            {order.recipient_address}
          </p>
        </div>

        <div className="action-buttons">
          <button className="btn-primary" onClick={() => navigate(`/order/${order.order_id}`)}>
            查看訂單詳情
          </button>
          <button className="btn-secondary" onClick={() => navigate('/')}>
            {t.cart.continueShopping}
          </button>
        </div>
      </div>
    </div>
  );
};

export default OrderSuccessPage;
