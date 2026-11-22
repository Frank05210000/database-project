// RSS：依日／週／月統計各商店銷售（BR-23 比例分攤）與熱銷商品
import { useMemo, useState } from 'react';
import { formatMoney, get } from '../../api/client';
import type { SalesRow, Store, TopProductRow } from '../../api/types';
import {
  addDays, Alert, BarList, Card, Empty, ErrorAlert, Field, isoDate, Loading, PageHeader, Tabs, useLoad,
} from '../../components/Backoffice';

type Period = 'day' | 'week' | 'month';
const PERIOD_LABEL: Record<Period, string> = { day: '日', week: '週', month: '月' };
const DEFAULT_RANGE: Record<Period, number> = { day: -13, week: -83, month: -364 };

export default function ReportsPage() {
  const [period, setPeriod] = useState<Period>('day');
  const [from, setFrom] = useState(addDays(DEFAULT_RANGE.day));
  const [to, setTo] = useState(isoDate());
  const [storeId, setStoreId] = useState('');

  const stores = useLoad(() => get<Store[]>('/stores/'), []);
  const sales = useLoad(
    () => get<SalesRow[]>('/reports/sales', { period, date_from: from, date_to: to, store_id: storeId }),
    [period, from, to, storeId],
  );
  const top = useLoad(
    () => get<TopProductRow[]>('/reports/top-products', { date_from: from, date_to: to, store_id: storeId, limit: 10 }),
    [from, to, storeId],
  );

  const changePeriod = (p: Period) => {
    setPeriod(p);
    setFrom(addDays(DEFAULT_RANGE[p]));
    setTo(isoDate());
  };

  const byStore = useMemo(() => {
    const m = new Map<string, { sales: number; orders: number }>();
    (sales.data ?? []).forEach((r) => {
      const cur = m.get(r.store_name) ?? { sales: 0, orders: 0 };
      cur.sales += r.sales_total;
      cur.orders += r.order_count;
      m.set(r.store_name, cur);
    });
    return Array.from(m.entries()).map(([label, v]) => ({ label, value: v.sales, orders: v.orders })).sort((a, b) => b.value - a.value);
  }, [sales.data]);

  const byPeriod = useMemo(() => {
    const m = new Map<string, { label: string; value: number }>();
    (sales.data ?? []).forEach((r) => {
      const cur = m.get(r.period_start) ?? { label: r.period_label, value: 0 };
      cur.value += r.sales_total;
      m.set(r.period_start, cur);
    });
    return Array.from(m.entries()).sort(([a], [b]) => a.localeCompare(b)).map(([, v]) => v);
  }, [sales.data]);

  const totals = useMemo(
    () => (sales.data ?? []).reduce((acc, r) => ({ orders: acc.orders + r.order_count, sales: acc.sales + r.sales_total }), { orders: 0, sales: 0 }),
    [sales.data],
  );

  return (
    <>
      <PageHeader title="銷售報表" subtitle="依期間統計各商店的訂單數與銷售總額" />
      <Card>
        <div className="bo-toolbar">
          <Field label="統計週期">
            <Tabs<Period> value={period} onChange={changePeriod} options={(['day', 'week', 'month'] as Period[]).map((p) => ({ value: p, label: PERIOD_LABEL[p] }))} />
          </Field>
          <Field label="起日"><input type="date" className="bo-input" value={from} onChange={(e) => setFrom(e.target.value)} /></Field>
          <Field label="迄日"><input type="date" className="bo-input" value={to} onChange={(e) => setTo(e.target.value)} /></Field>
          <Field label="商店">
            <select className="bo-select" value={storeId} onChange={(e) => setStoreId(e.target.value)}>
              <option value="">全部商店</option>
              {stores.data?.map((s) => <option key={s.store_id} value={s.store_id}>{s.name}</option>)}
            </select>
          </Field>
        </div>
        <Alert>
          已取消／已退貨的訂單不計入；一筆訂單含多間商店商品時，訂單總額依各店商品扣除特殊活動折扣後的金額比例分攤（BR-23）；部分退貨的訂單會扣除該項退款金額。
          「訂單數」為包含該商店商品的訂單筆數，因此各店加總可能大於實際訂單數。
        </Alert>
      </Card>

      <ErrorAlert error={sales.error} />
      {sales.loading && !sales.data ? <Loading /> : sales.data && (
        <>
          <div className="bo-grid bo-grid--2">
            <Card title="各商店銷售總額">
              <BarList rows={byStore} format={formatMoney} />
            </Card>
            <Card title={`每${PERIOD_LABEL[period]}銷售趨勢`}>
              <TrendChart rows={byPeriod} />
            </Card>
          </div>
          <Card title={`銷售明細（每${PERIOD_LABEL[period]}）`} extra={<span className="bo-muted" style={{ fontWeight: 400, fontSize: 13 }}>合計 {formatMoney(totals.sales)}</span>}>
            {sales.data.length === 0 ? <Empty>此期間沒有銷售資料</Empty> : (
              <div className="bo-table-wrap">
                <table className="bo-table">
                  <thead><tr><th>日期／期間</th><th>商店名稱</th><th className="num">訂單數</th><th className="num">銷售總額</th></tr></thead>
                  <tbody>
                    {sales.data.map((r) => (
                      <tr key={`${r.period_start}-${r.store_id}`}>
                        <td>{r.period_label}</td>
                        <td>{r.store_name}</td>
                        <td className="num">{r.order_count}</td>
                        <td className="num">{formatMoney(r.sales_total)}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr><td colSpan={2}>合計</td><td className="num">{totals.orders}</td><td className="num">{formatMoney(totals.sales)}</td></tr>
                  </tfoot>
                </table>
              </div>
            )}
          </Card>
        </>
      )}

      <Card title="熱銷商品 Top 10">
        <ErrorAlert error={top.error} />
        {top.loading && !top.data ? <Loading /> : !top.data || top.data.length === 0 ? <Empty>此期間沒有銷售資料</Empty> : (
          <div className="bo-table-wrap">
            <table className="bo-table">
              <thead><tr><th>#</th><th>商品</th><th>商店</th><th className="num">銷售數量</th><th className="num">營收</th></tr></thead>
              <tbody>
                {top.data.map((r, i) => (
                  <tr key={r.product_id}>
                    <td>{i + 1}</td>
                    <td className="bo-cell-main">{r.product_name}</td>
                    <td>{r.store_name}</td>
                    <td className="num">{r.quantity}</td>
                    <td className="num">{formatMoney(r.revenue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
}

/** 期間銷售趨勢（inline SVG 長條） */
function TrendChart({ rows }: { rows: { label: string; value: number }[] }) {
  if (rows.length === 0) return <Empty />;
  const W = 520, H = 200, pad = 24;
  const max = Math.max(1, ...rows.map((r) => r.value));
  const bw = (W - pad * 2) / rows.length;
  const labelEvery = Math.ceil(rows.length / 8);
  return (
    <svg viewBox={`0 0 ${W} ${H + 24}`} width="100%" role="img" aria-label="銷售趨勢">
      <line x1={pad} y1={H} x2={W - pad} y2={H} stroke="#f0dccf" />
      {rows.map((r, i) => {
        const h = (r.value / max) * (H - pad);
        const x = pad + i * bw + bw * 0.15;
        return (
          <g key={i}>
            <rect x={x} y={H - h} width={bw * 0.7} height={Math.max(h, 1)} rx={3} fill="#d36b55" opacity={0.85}>
              <title>{`${r.label}：${formatMoney(r.value)}`}</title>
            </rect>
            {i % labelEvery === 0 && (
              <text x={x + bw * 0.35} y={H + 16} textAnchor="middle" fontSize="10" fill="#9a7d70">{r.label}</text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
