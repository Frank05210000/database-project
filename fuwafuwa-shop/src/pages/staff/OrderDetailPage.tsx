// OMS：訂單明細、金額拆解、狀態歷程，推進到下一狀態（BR-19、BR-25）
import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { DISCOUNT_TYPE_LABEL, formatDateTime, formatMoney, get, ORDER_STATUS_LABEL, post } from '../../api/client';
import type { Order } from '../../api/types';
import {
  Alert, Card, ConfirmModal, ErrorAlert, Loading, OrderStatusBadge, PageHeader, ReturnStatusBadge, useLoad, useToast,
} from '../../components/Backoffice';

const FLOW = ['received', 'processing', 'shipping', 'closed'];

export default function OrderDetailPage() {
  const { id } = useParams();
  const toast = useToast();
  const { data: order, setData, loading, error } = useLoad(() => get<Order>(`/orders/${id}`), [id]);
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);

  if (loading && !order) return <Loading />;
  if (!order) return <><Link to="/staff/orders" className="bo-back">← 返回訂單列表</Link><ErrorAlert error={error} /></>;

  const pendingReturn = order.return_request?.status === 'pending';
  const isFinal = !order.next_status;
  const disabledReason = pendingReturn
    ? '此訂單有待審核的退貨申請，依 BR-25 須先完成退貨審核才能變更訂單狀態。'
    : isFinal
      ? `訂單已是最終狀態「${ORDER_STATUS_LABEL[order.status]}」，依 BR-19 不能再變更。`
      : null;

  const advance = async () => {
    if (!order.next_status) return;
    setBusy(true);
    try {
      const updated = await post<Order>(`/orders/${order.order_id}/status`, { status: order.next_status });
      setData(updated);
      toast.success(`訂單 #${order.order_id} 已更新為「${ORDER_STATUS_LABEL[updated.status]}」`);
      setConfirming(false);
    } catch (e) {
      toast.error(e);
    } finally {
      setBusy(false);
    }
  };

  const stepIdx = FLOW.indexOf(order.status);
  const shippingPaid = order.shipping_fee - order.shipping_discount;
  const itemDiscountTotal = order.discount_total - order.shipping_discount;

  return (
    <>
      <Link to="/staff/orders" className="bo-back">← 返回訂單列表</Link>
      <PageHeader
        title={`訂單 #${order.order_id}`}
        subtitle={<>下單時間 {formatDateTime(order.order_time)} · 付款時間 {formatDateTime(order.paid_at)}</>}
        actions={
          <>
            <OrderStatusBadge status={order.status} />
            <button className="bo-btn" disabled={!!disabledReason || busy} onClick={() => setConfirming(true)} title={disabledReason ?? ''}>
              推進到下一狀態{order.next_status ? `：${ORDER_STATUS_LABEL[order.next_status]}` : ''} →
            </button>
          </>
        }
      />
      {disabledReason && <Alert kind={pendingReturn ? 'warn' : 'info'}>{disabledReason}</Alert>}

      <Card title="訂單進度">
        {stepIdx >= 0 ? (
          <div className="bo-steps">
            {FLOW.map((s, i) => (
              <div key={s} className={`bo-step ${i <= stepIdx ? 'done' : ''} ${i === stepIdx ? 'current' : ''}`}>{ORDER_STATUS_LABEL[s]}</div>
            ))}
          </div>
        ) : (
          <p>此訂單目前為 <OrderStatusBadge status={order.status} />，流程已結束。</p>
        )}
        <p className="bo-muted" style={{ margin: 0, fontSize: 12 }}>BR-19：狀態只能依序推進 已接單 → 處理中 → 配送中 → 已完成，不可跳過或倒退。</p>
      </Card>

      <div className="bo-grid bo-grid--2">
        <Card title="顧客與收件資訊">
          <dl className="bo-dl">
            <dt>顧客</dt><dd>{order.customer.name}（{order.customer.loginid}）</dd>
            <dt>收件人</dt><dd>{order.recipient_name}</dd>
            <dt>電話</dt><dd>{order.recipient_phone}</dd>
            <dt>地址</dt><dd>{order.recipient_address}</dd>
          </dl>
        </Card>
        <Card title="狀態歷程">
          <ul className="bo-timeline">
            {order.history.map((h) => (
              <li key={h.seq_no}>
                <OrderStatusBadge status={h.status} /> <span className="bo-muted">{formatDateTime(h.changed_at)}</span>
                <div className="bo-cell-sub">由 {h.changed_by_name || '系統'}</div>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <Card title="訂單明細">
        <div className="bo-table-wrap">
          <table className="bo-table">
            <thead><tr><th>#</th><th>商品</th><th>商店</th><th className="num">單價</th><th className="num">數量</th><th className="num">小計</th><th className="num">活動折扣</th></tr></thead>
            <tbody>
              {order.items.map((it) => (
                <tr key={it.item_no}>
                  <td>{it.item_no}</td>
                  <td className="bo-cell-main">{it.product_name}</td>
                  <td>{it.store_name}</td>
                  <td className="num">{formatMoney(it.unit_price)}</td>
                  <td className="num">{it.quantity}</td>
                  <td className="num">{formatMoney(it.line_subtotal)}</td>
                  <td className="num">{it.event_discount ? `−${formatMoney(it.event_discount)}` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="bo-grid bo-grid--2 bo-mt">
          <div>
            <h3 style={{ fontSize: 14, margin: '0 0 8px' }}>套用的折扣</h3>
            {order.discounts.length === 0 ? <p className="bo-muted">無</p> : (
              <ul style={{ paddingLeft: 18, margin: 0 }}>
                {order.discounts.map((d) => (
                  <li key={d.discount_code}>
                    <b>{d.discount_code}</b> {DISCOUNT_TYPE_LABEL[d.discount_type]}：{d.description}（−{formatMoney(d.amount)}）
                  </li>
                ))}
              </ul>
            )}
          </div>
          <table className="bo-amounts">
            <tbody>
              <tr><td>商品小計</td><td>{formatMoney(order.subtotal)}</td></tr>
              <tr><td>商品折扣（活動＋季節）</td><td className="neg">−{formatMoney(itemDiscountTotal)}</td></tr>
              <tr><td>稅金</td><td>{formatMoney(order.tax)}</td></tr>
              <tr><td>運費</td><td>{formatMoney(order.shipping_fee)}</td></tr>
              {order.shipping_discount > 0 && <tr><td>運費折扣</td><td className="neg">−{formatMoney(order.shipping_discount)}</td></tr>}
              <tr><td className="bo-muted">（折扣合計 {formatMoney(order.discount_total)}，實付運費 {formatMoney(shippingPaid)}）</td><td></td></tr>
              <tr className="total"><td>訂單總額</td><td>{formatMoney(order.total)}</td></tr>
            </tbody>
          </table>
        </div>
      </Card>

      {order.return_request && (
        <Card title="退貨申請" extra={<Link className="bo-link" to={`/staff/returns/${order.return_request.return_id}`}>前往審核 →</Link>}>
          <dl className="bo-dl">
            <dt>狀態</dt><dd><ReturnStatusBadge status={order.return_request.status} /></dd>
            <dt>申請時間</dt><dd>{formatDateTime(order.return_request.requested_at)}</dd>
            <dt>原因</dt><dd>{order.return_request.reason}</dd>
            {order.return_request.refund_total != null && <><dt>退款金額</dt><dd>{formatMoney(order.return_request.refund_total)}</dd></>}
            {order.return_request.reject_reason && <><dt>拒絕原因</dt><dd>{order.return_request.reject_reason}</dd></>}
          </dl>
        </Card>
      )}

      {confirming && order.next_status && (
        <ConfirmModal
          title="推進訂單狀態"
          busy={busy}
          confirmLabel="確認推進"
          onClose={() => setConfirming(false)}
          onConfirm={advance}
          message={<p>將訂單 #{order.order_id} 從「{ORDER_STATUS_LABEL[order.status]}」推進到「<b>{ORDER_STATUS_LABEL[order.next_status]}</b>」？系統會自動記錄狀態歷程。</p>}
        />
      )}
    </>
  );
}
