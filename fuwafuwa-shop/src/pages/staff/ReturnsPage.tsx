// 退貨審核：核准（依 BR-26 計算退款）或拒絕（須填原因）
import { useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { formatDateTime, formatMoney, get, post, RETURN_STATUS_LABEL } from '../../api/client';
import type { ReturnRequest } from '../../api/types';
import {
  Alert, Card, ConfirmModal, Empty, ErrorAlert, Field, Loading, Modal, OrderStatusBadge, PageHeader, ReturnStatusBadge, useLoad, useToast,
} from '../../components/Backoffice';

export default function ReturnsPage() {
  const { id } = useParams();
  return id ? <ReturnDetail id={id} /> : <ReturnList />;
}

function ReturnList() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const status = params.get('status') ?? '';
  const { data, loading, error } = useLoad(() => get<ReturnRequest[]>('/returns/', { status }), [status]);

  return (
    <>
      <PageHeader title="退貨審核" subtitle="處理中、配送中或已完成的訂單可申請退貨，每筆訂單限一次（BR-25）；核准後依 BR-26 計算退款金額" />
      <Card>
        <div className="bo-toolbar">
          <Field label="狀態">
            <select className="bo-select" value={status} onChange={(e) => setParams(e.target.value ? { status: e.target.value } : {}, { replace: true })}>
              <option value="">全部</option>
              {Object.entries(RETURN_STATUS_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </Field>
        </div>
        <ErrorAlert error={error} />
        {loading && !data ? <Loading /> : !data || data.length === 0 ? <Empty>沒有退貨申請</Empty> : (
          <div className="bo-table-wrap">
            <table className="bo-table">
              <thead>
                <tr><th>退貨單</th><th>訂單</th><th>申請時間</th><th>顧客</th><th>原因</th><th className="num">退貨件數</th><th className="num">退款</th><th>狀態</th></tr>
              </thead>
              <tbody>
                {data.map((r) => (
                  <tr key={r.return_id} className="is-clickable" onClick={() => navigate(`/staff/returns/${r.return_id}`)}>
                    <td className="bo-cell-main">R{r.return_id}</td>
                    <td>#{r.order_id}</td>
                    <td>{formatDateTime(r.requested_at)}</td>
                    <td>{r.customer.name}<div className="bo-cell-sub">{r.customer.loginid}</div></td>
                    <td style={{ maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={r.reason}>{r.reason}</td>
                    <td className="num">{r.items.reduce((s, i) => s + i.return_qty, 0)}</td>
                    <td className="num">{r.refund_total != null ? formatMoney(r.refund_total) : '—'}</td>
                    <td><ReturnStatusBadge status={r.status} /></td>
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

function ReturnDetail({ id }: { id: string }) {
  const toast = useToast();
  const { data: ret, setData, loading, error } = useLoad(() => get<ReturnRequest>(`/returns/${id}`), [id]);
  const [mode, setMode] = useState<'approve' | 'reject' | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<unknown>(null);
  const [justApproved, setJustApproved] = useState(false);

  if (loading && !ret) return <Loading />;
  if (!ret) return <><Link to="/staff/returns" className="bo-back">← 返回退貨列表</Link><ErrorAlert error={error} /></>;

  const approve = async () => {
    setBusy(true);
    try {
      const r = await post<ReturnRequest>(`/returns/${ret.return_id}/approve`);
      setData(r);
      setJustApproved(true);
      setMode(null);
      toast.success(`已核准退貨，退款 ${formatMoney(r.refund_total)}`);
    } catch (e) {
      toast.error(e);
    } finally {
      setBusy(false);
    }
  };

  const reject = async () => {
    setBusy(true);
    setActionError(null);
    try {
      const r = await post<ReturnRequest>(`/returns/${ret.return_id}/reject`, { reject_reason: rejectReason.trim() });
      setData(r);
      setMode(null);
      toast.success('已拒絕退貨申請');
    } catch (e) {
      setActionError(e);
      toast.error(e);
    } finally {
      setBusy(false);
    }
  };

  const pending = ret.status === 'pending';

  return (
    <>
      <Link to="/staff/returns" className="bo-back">← 返回退貨列表</Link>
      <PageHeader
        title={`退貨申請 R${ret.return_id}`}
        subtitle={<>訂單 <Link className="bo-link" to={`/staff/orders/${ret.order_id}`}>#{ret.order_id}</Link> · 申請時間 {formatDateTime(ret.requested_at)}</>}
        actions={
          <>
            <ReturnStatusBadge status={ret.status} />
            {pending && (
              <>
                <button className="bo-btn bo-btn--danger" onClick={() => { setRejectReason(''); setActionError(null); setMode('reject'); }}>拒絕</button>
                <button className="bo-btn bo-btn--success" onClick={() => setMode('approve')}>核准退貨</button>
              </>
            )}
          </>
        }
      />
      {justApproved && ret.refund_total != null && (
        <Alert kind="success">已核准，依 BR-26 計算的退款總額為 <b>{formatMoney(ret.refund_total)}</b>，退貨商品已回補庫存{ret.order_status === 'returned' ? '，訂單全部退貨，狀態改為「已退貨」' : '（部分退貨，訂單狀態不變）'}。</Alert>
      )}

      <div className="bo-grid bo-grid--2">
        <Card title="申請資訊">
          <dl className="bo-dl">
            <dt>顧客</dt><dd>{ret.customer.name}（{ret.customer.loginid}）</dd>
            <dt>訂單狀態</dt><dd><OrderStatusBadge status={ret.order_status} /></dd>
            <dt>訂單總額</dt><dd>{formatMoney(ret.order_total)}</dd>
            <dt>退貨原因</dt><dd style={{ whiteSpace: 'pre-wrap' }}>{ret.reason}</dd>
          </dl>
        </Card>
        <Card title="審核結果">
          {pending ? <p className="bo-muted">尚未審核。</p> : (
            <dl className="bo-dl">
              <dt>結果</dt><dd><ReturnStatusBadge status={ret.status} /></dd>
              <dt>處理人員</dt><dd>{ret.processed_by_name ?? '—'}</dd>
              <dt>處理時間</dt><dd>{formatDateTime(ret.processed_at)}</dd>
              {ret.refund_total != null && <><dt>退款總額</dt><dd><b>{formatMoney(ret.refund_total)}</b></dd></>}
              {ret.reject_reason && <><dt>拒絕原因</dt><dd>{ret.reject_reason}</dd></>}
            </dl>
          )}
        </Card>
      </div>

      <Card title="退貨品項">
        <div className="bo-table-wrap">
          <table className="bo-table">
            <thead><tr><th>#</th><th>商品</th><th className="num">單價</th><th className="num">購買數量</th><th className="num">退貨數量</th><th className="num">退款金額</th></tr></thead>
            <tbody>
              {ret.items.map((it) => (
                <tr key={it.item_no}>
                  <td>{it.item_no}</td>
                  <td className="bo-cell-main">{it.product_name}</td>
                  <td className="num">{formatMoney(it.unit_price)}</td>
                  <td className="num">{it.quantity}</td>
                  <td className="num"><b>{it.return_qty}</b></td>
                  <td className="num">{it.refund_amount != null ? formatMoney(it.refund_amount) : '—'}</td>
                </tr>
              ))}
            </tbody>
            {ret.refund_total != null && (
              <tfoot>
                <tr><td colSpan={5}>退款總額（BR-26）</td><td className="num">{formatMoney(ret.refund_total)}</td></tr>
              </tfoot>
            )}
          </table>
        </div>
        <p className="bo-muted bo-mt" style={{ fontSize: 12 }}>
          BR-26：每項退款＝（訂單總額 − 實付運費）× 該項扣除特殊活動折扣後的金額 ÷ 全部商品扣除特殊活動折扣後的金額；部分數量退貨依退貨數量比例計算。運費不退，唯處理中訂單全部退貨時一併退還運費。
        </p>
      </Card>

      {mode === 'approve' && (
        <ConfirmModal
          title="核准退貨"
          busy={busy}
          confirmLabel="核准"
          onClose={() => setMode(null)}
          onConfirm={approve}
          message={<p>核准退貨申請 R{ret.return_id}？系統將依 BR-26 計算每項退款金額並回補庫存；若訂單全部退貨，訂單 #{ret.order_id} 會改為「已退貨」。</p>}
        />
      )}
      {mode === 'reject' && (
        <Modal
          title="拒絕退貨"
          onClose={() => setMode(null)}
          onSubmit={reject}
          footer={
            <>
              <button type="button" className="bo-btn bo-btn--ghost" onClick={() => setMode(null)}>取消</button>
              <button type="submit" className="bo-btn bo-btn--danger" disabled={busy || !rejectReason.trim()}>確認拒絕</button>
            </>
          }
        >
          <ErrorAlert error={actionError} />
          <Field label="拒絕原因" required hint="會顯示給顧客">
            <textarea className="bo-textarea" value={rejectReason} onChange={(e) => setRejectReason(e.target.value)} autoFocus />
          </Field>
        </Modal>
      )}
    </>
  );
}
