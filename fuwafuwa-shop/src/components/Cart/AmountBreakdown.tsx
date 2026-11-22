import React from 'react';
import { DISCOUNT_TYPE_LABEL, formatMoney } from '../../api/client';
import type { AppliedDiscount, Order, Quote } from '../../api/types';
import { useLanguage } from '../../i18n';

interface Amounts {
  subtotal: number;
  eventDiscount: number;
  seasonalDiscount: number;
  tax: number;
  shippingFee: number;
  shippingDiscount: number;
  total: number;
  discounts: AppliedDiscount[];
}

export const amountsFromQuote = (q: Quote): Amounts => ({
  subtotal: q.subtotal,
  eventDiscount: q.event_discount,
  seasonalDiscount: q.seasonal_discount,
  tax: q.tax,
  shippingFee: q.shipping_fee,
  shippingDiscount: q.shipping_discount,
  total: q.total,
  discounts: q.applied_discounts,
});

const sumType = (list: AppliedDiscount[], type: string) =>
  list.filter((d) => d.discount_type === type).reduce((s, d) => s + d.amount, 0);

export const amountsFromOrder = (o: Order): Amounts => ({
  subtotal: o.subtotal,
  eventDiscount: sumType(o.discounts, 'special_event'),
  seasonalDiscount: sumType(o.discounts, 'seasonal'),
  tax: o.tax,
  shippingFee: o.shipping_fee,
  shippingDiscount: o.shipping_discount,
  total: o.total,
  discounts: o.discounts,
});

/** 金額明細（SCS-F-004）：小計、特殊活動折扣、季節性折扣、稅 5%、運費、運費折扣、總額 */
export const AmountBreakdown: React.FC<{ amounts: Amounts; taxRate?: number }> = ({ amounts: a, taxRate = 0.05 }) => {
  const { t } = useLanguage();
  const minus = (n: number) => (n > 0 ? `− ${formatMoney(n)}` : formatMoney(0));
  return (
    <div className="fw-breakdown">
      <div className="fw-breakdown__row">
        <span>{t.cart.subtotal}</span>
        <span>{formatMoney(a.subtotal)}</span>
      </div>
      <div className="fw-breakdown__row fw-breakdown__row--discount">
        <span>{t.cart.eventDiscount}</span>
        <span>{minus(a.eventDiscount)}</span>
      </div>
      <div className="fw-breakdown__row fw-breakdown__row--discount">
        <span>{t.cart.seasonalDiscount}</span>
        <span>{minus(a.seasonalDiscount)}</span>
      </div>
      <div className="fw-breakdown__row">
        <span>
          {t.cart.tax}（{Math.round(Number(taxRate) * 100)}%）
        </span>
        <span>{formatMoney(a.tax)}</span>
      </div>
      <div className="fw-breakdown__row">
        <span>{t.cart.shippingFee}</span>
        <span>{formatMoney(a.shippingFee)}</span>
      </div>
      <div className="fw-breakdown__row fw-breakdown__row--discount">
        <span>{t.cart.shippingDiscount}</span>
        <span>{minus(a.shippingDiscount)}</span>
      </div>
      <div className="fw-breakdown__row fw-breakdown__row--total">
        <span>{t.cart.total}</span>
        <span>{formatMoney(a.total)}</span>
      </div>
      {a.discounts.length > 0 && (
        <>
          <div style={{ marginTop: 10, fontWeight: 700 }}>{t.cart.appliedDiscounts}</div>
          <ul className="fw-discount-list">
            {a.discounts.map((d, i) => (
              <li key={`${d.discount_code}-${i}`}>
                <span>
                  <code>{d.discount_code}</code> {DISCOUNT_TYPE_LABEL[d.discount_type] ?? d.discount_type}｜
                  {d.description}
                </span>
                <span style={{ color: '#2e7d32', whiteSpace: 'nowrap' }}>− {formatMoney(d.amount)}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
};
