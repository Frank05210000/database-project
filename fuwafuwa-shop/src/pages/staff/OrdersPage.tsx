// OMS：工作人員查詢所有訂單
import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { formatDateTime, formatMoney, get, ORDER_STATUS_LABEL } from '../../api/client';
import type { OrderSummary } from '../../api/types';
import { Card, Empty, ErrorAlert, Field, Loading, OrderStatusBadge, PageHeader, ReturnStatusBadge, useLoad } from '../../components/Backoffice';

export default function OrdersPage() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const status = params.get('status') ?? '';
  const dateFrom = params.get('date_from') ?? '';
  const dateTo = params.get('date_to') ?? '';
  const qApplied = params.get('q') ?? '';
  const [q, setQ] = useState(qApplied);

  const setParam = (k: string, v: string) => {
    const next = new URLSearchParams(params);
    if (v) next.set(k, v); else next.delete(k);
    setParams(next, { replace: true });
  };

  const { data, loading, error } = useLoad(
    () => get<OrderSummary[]>('/orders/', { status, date_from: dateFrom, date_to: dateTo, q: qApplied }),
    [status, dateFrom, dateTo, qApplied],
  );

  return (
    <>
      <PageHeader title="訂單管理" subtitle="依狀態、日期或顧客查詢訂單，點選列查看明細並推進狀態（BR-19）" />
      <Card>
        <form className="bo-toolbar" onSubmit={(e) => { e.preventDefault(); setParam('q', q.trim()); }}>
          <Field label="狀態">
            <select className="bo-select" value={status} onChange={(e) => setParam('status', e.target.value)}>
              <option value="">全部狀態</option>
              {Object.entries(ORDER_STATUS_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </Field>
          <Field label="起日"><input type="date" className="bo-input" value={dateFrom} onChange={(e) => setParam('date_from', e.target.value)} /></Field>
          <Field label="迄日"><input type="date" className="bo-input" value={dateTo} onChange={(e) => setParam('date_to', e.target.value)} /></Field>
          <Field label="關鍵字">
            <input className="bo-input" placeholder="訂單編號、顧客帳號或姓名" value={q} onChange={(e) => setQ(e.target.value)} style={{ minWidth: 220 }} />
          </Field>
          <button className="bo-btn bo-btn--ghost" type="submit">搜尋</button>
          {(status || dateFrom || dateTo || qApplied) && (
            <button type="button" className="bo-btn bo-btn--ghost" onClick={() => { setQ(''); setParams({}, { replace: true }); }}>清除</button>
          )}
        </form>
        <ErrorAlert error={error} />
        {loading && !data ? <Loading /> : !data || data.length === 0 ? <Empty>沒有符合條件的訂單</Empty> : (
          <div className="bo-table-wrap">
            <table className="bo-table">
              <thead>
                <tr><th>訂單編號</th><th>下單時間</th><th>顧客</th><th className="num">品項數</th><th className="num">總金額</th><th>狀態</th><th>退貨</th></tr>
              </thead>
              <tbody>
                {data.map((o) => (
                  <tr key={o.order_id} className="is-clickable" onClick={() => navigate(`/staff/orders/${o.order_id}`)}>
                    <td className="bo-cell-main">#{o.order_id}</td>
                    <td>{formatDateTime(o.order_time)}</td>
                    <td>{o.customer.name}<div className="bo-cell-sub">{o.customer.loginid}</div></td>
                    <td className="num">{o.item_count}</td>
                    <td className="num">{formatMoney(o.total)}</td>
                    <td><OrderStatusBadge status={o.status} /></td>
                    <td>{o.return_status ? <ReturnStatusBadge status={o.return_status} /> : <span className="bo-muted">—</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {data && <p className="bo-muted bo-mt">共 {data.length} 筆訂單</p>}
      </Card>
    </>
  );
}
