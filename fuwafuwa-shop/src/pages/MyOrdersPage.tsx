import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useOrders } from '../hooks/useOrders';
import { useLanguage } from '../i18n';
import { formatDateTime, formatMoney, ORDER_STATUS_LABEL, RETURN_STATUS_LABEL } from '../api/client';
import './MyOrdersPage.css';

const MyOrdersPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const { user, loading: authLoading } = useAuth();
  const { orders, stats, loading, error } = useOrders();

  if (!authLoading && !user) {
    return (
      <div className="my-orders-page">
        <div className="orders-container">
          <h2>請先登入</h2>
          <button onClick={() => navigate('/login', { state: { from: '/my-orders' } })}>前往登入</button>
        </div>
      </div>
    );
  }

  return (
    <div className="my-orders-page">
      <div className="orders-container">
        <h1>{t.orders.title}</h1>

        <div className="order-stats">
          <div className="stat-card">
            <div className="stat-number">{stats.total}</div>
            <div className="stat-label">{t.orders.statTotal}</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{stats.active}</div>
            <div className="stat-label">{t.orders.statActive}</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{stats.closed}</div>
            <div className="stat-label">{t.orders.statClosed}</div>
          </div>
          <div className="stat-card highlight">
            <div className="stat-number">{formatMoney(stats.totalSpent)}</div>
            <div className="stat-label">{t.orders.statSpent}</div>
          </div>
        </div>

        {error && <div className="fw-error">{error}</div>}

        {loading ? (
          <div className="loading">{t.product.loading}</div>
        ) : orders.length === 0 ? (
          <div className="empty-orders">
            <p>{t.orders.empty}</p>
            <button onClick={() => navigate('/')}>{t.orders.startShopping}</button>
          </div>
        ) : (
          <div className="orders-list">
            {orders.map((order) => (
              <div key={order.order_id} className="order-card">
                <div className="order-header">
                  <div className="order-number">
                    <span className="label">{t.orders.orderNo}：</span>
                    <span className="value">#{order.order_id}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    {order.has_return && order.return_status && (
                      <span className="fw-return-tag">
                        {t.orders.returnStatus}：{RETURN_STATUS_LABEL[order.return_status] ?? order.return_status}
                      </span>
                    )}
                    <div className={`order-status status-${order.status}`}>
                      {ORDER_STATUS_LABEL[order.status] ?? order.status}
                    </div>
                  </div>
                </div>

                <div className="order-footer">
                  <div className="order-info">
                    <div className="info-item">
                      <span className="label">{t.orders.orderTime}：</span>
                      <span className="value">{formatDateTime(order.order_time)}</span>
                    </div>
                    <div className="info-item">
                      <span className="label">{t.orders.itemCount}：</span>
                      <span className="value">{order.item_count}</span>
                    </div>
                  </div>
                  <div className="order-total">
                    <span className="label">{t.orders.total}：</span>
                    <span className="amount">{formatMoney(order.total)}</span>
                  </div>
                </div>

                <div className="order-actions">
                  <button className="btn-details" onClick={() => navigate(`/order/${order.order_id}`)}>
                    {t.orders.details}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MyOrdersPage;
