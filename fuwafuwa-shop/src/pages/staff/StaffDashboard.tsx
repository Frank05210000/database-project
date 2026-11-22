import { useState } from 'react';
import { Link } from 'react-router-dom';
import { formatMoney, get, ORDER_STATUS_LABEL } from '../../api/client';
import type { ReportSummary } from '../../api/types';
import { addDays, BarList, Card, ErrorAlert, Field, isoDate, KpiCard, Loading, PageHeader, useLoad } from '../../components/Backoffice';
import { useAuth } from '../../contexts/AuthContext';

const STATUS_ORDER = ['received', 'processing', 'shipping', 'closed', 'cancelled', 'returned'];

export default function StaffDashboard() {
  const { user } = useAuth();
  const [from, setFrom] = useState(addDays(-30));
  const [to, setTo] = useState(isoDate());
  const { data, loading, error } = useLoad(
    () => get<ReportSummary>('/reports/summary', { date_from: from, date_to: to }),
    [from, to],
  );

  return (
    <>
      <PageHeader
        title={`你好，${user?.name ?? ''}`}
        subtitle="今日營運概況與待辦事項"
        actions={
          <div className="bo-toolbar" style={{ margin: 0 }}>
            <Field label="起日"><input type="date" className="bo-input" value={from} onChange={(e) => setFrom(e.target.value)} /></Field>
            <Field label="迄日"><input type="date" className="bo-input" value={to} onChange={(e) => setTo(e.target.value)} /></Field>
          </div>
        }
      />
      <ErrorAlert error={error} />
      {loading && !data ? <Loading /> : data && (
        <>
          <div className="bo-grid bo-grid--kpi">
            <KpiCard label="訂單數" value={data.order_count.toLocaleString('zh-TW')} icon="🧾" />
            <KpiCard label="銷售總額" value={formatMoney(data.sales_total)} icon="💰" accent="#e3f3e8" />
            <KpiCard label="下單顧客數" value={data.customer_count.toLocaleString('zh-TW')} icon="🐾" accent="#e3eef9" />
            <KpiCard
              label="待審核退貨"
              value={data.pending_returns}
              icon="↩️"
              accent="#fdf1d8"
              hint={data.pending_returns > 0 ? <Link className="bo-link" to="/staff/returns?status=pending">前往審核 →</Link> : '目前沒有待辦'}
            />
          </div>
          <div className="bo-grid bo-grid--2">
            <Card title="各狀態訂單數">
              <BarList
                rows={STATUS_ORDER.map((s) => ({
                  label: ORDER_STATUS_LABEL[s] ?? s,
                  value: data.orders_by_status[s] ?? 0,
                }))}
                format={(n) => `${n} 筆`}
              />
            </Card>
            <Card title="快速前往">
              <div className="bo-quick">
                <Link to="/staff/orders?status=received">🧾 待處理訂單</Link>
                <Link to="/staff/returns?status=pending">↩️ 退貨審核</Link>
                <Link to="/staff/products">📦 商品與庫存</Link>
                <Link to="/staff/discounts">🏷️ 折扣管理</Link>
                <Link to="/staff/reports">📊 銷售報表</Link>
              </div>
            </Card>
          </div>
        </>
      )}
    </>
  );
}
