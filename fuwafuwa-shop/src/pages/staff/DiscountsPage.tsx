// DMS：折扣政策管理（運費、季節性、特殊活動），代碼由系統產生（BR-18），期間重疊檢查（BR-13 / DMS-F-008）
import { useMemo, useState } from 'react';
import { ApiError, del, DISCOUNT_TYPE_LABEL, formatMoney, get, post, put } from '../../api/client';
import type { Discount, DiscountInput, DiscountType, Product } from '../../api/types';
import {
  Alert, Badge, Card, Empty, ErrorAlert, Field, formatDate, isoDate, addDays, Loading, Modal, PageHeader, useLoad, useToast,
} from '../../components/Backoffice';

const TYPES: DiscountType[] = ['shipping', 'seasonal', 'special_event'];
const TYPE_TONE: Record<DiscountType, 'blue' | 'amber' | 'rose'> = { shipping: 'blue', seasonal: 'amber', special_event: 'rose' };
const CODE_PREFIX: Record<DiscountType, string> = { shipping: 'SHP', seasonal: 'SEA', special_event: 'EVT' };

interface FormState {
  code: string | null;
  discount_type: DiscountType;
  description: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
  min_amount: string;
  pct: string; // 折抵百分比（5 → rate 0.05）
  eventMode: 'rate' | 'bxgy';
  buy_qty: string;
  free_qty: string;
  product_ids: number[];
}

const newForm = (type: DiscountType = 'seasonal'): FormState => ({
  code: null, discount_type: type, description: '', start_date: isoDate(), end_date: addDays(30), is_active: true,
  min_amount: '', pct: '', eventMode: 'rate', buy_qty: '', free_qty: '', product_ids: [],
});

const fromDiscount = (d: Discount): FormState => ({
  code: d.discount_code, discount_type: d.discount_type, description: d.description,
  start_date: d.start_date.slice(0, 10), end_date: d.end_date.slice(0, 10), is_active: d.is_active,
  min_amount: d.min_amount != null ? String(d.min_amount) : '',
  pct: d.rate != null ? String(Math.round(Number(d.rate) * 10000) / 100) : '',
  eventMode: d.buy_qty != null ? 'bxgy' : 'rate',
  buy_qty: d.buy_qty != null ? String(d.buy_qty) : '', free_qty: d.free_qty != null ? String(d.free_qty) : '',
  product_ids: d.products.map((p) => p.product_id),
});

const num = (s: string): number | null => (s.trim() === '' ? null : Number(s));

function toInput(f: FormState): DiscountInput {
  const base: DiscountInput = {
    discount_type: f.discount_type, description: f.description.trim(), start_date: f.start_date, end_date: f.end_date,
    is_active: f.is_active, rate: null, min_amount: null, buy_qty: null, free_qty: null,
  };
  const rate = num(f.pct) == null ? null : Math.round(Number(f.pct) * 100) / 10000;
  if (f.discount_type === 'shipping') base.min_amount = num(f.min_amount);
  if (f.discount_type === 'seasonal') base.rate = rate;
  if (f.discount_type === 'special_event') {
    if (f.eventMode === 'rate') base.rate = rate;
    else { base.buy_qty = num(f.buy_qty); base.free_qty = num(f.free_qty); }
    base.product_ids = f.product_ids;
  }
  return base;
}

export const describeRule = (d: Pick<Discount, 'discount_type' | 'rate' | 'min_amount' | 'buy_qty' | 'free_qty'>): string => {
  if (d.discount_type === 'shipping') return d.min_amount != null ? `滿 ${formatMoney(d.min_amount)} 免運` : '免運';
  if (d.rate != null) {
    const pct = Math.round(Number(d.rate) * 10000) / 100;
    const keep = Math.round((1 - Number(d.rate)) * 1000) / 10; // 95、90、87.5
    const zhe = keep % 10 === 0 ? String(keep / 10) : String(keep).replace('.', '');
    return `折抵 ${pct}%（${zhe} 折）`;
  }
  if (d.buy_qty != null && d.free_qty != null) return `買 ${d.buy_qty} 送 ${d.free_qty}`;
  return '—';
};

export default function DiscountsPage() {
  const toast = useToast();
  const [type, setType] = useState('');
  const [activeOn, setActiveOn] = useState('');
  const [q, setQ] = useState('');
  const [qApplied, setQApplied] = useState('');
  const list = useLoad(() => get<Discount[]>('/discounts/', { type, active_on: activeOn, q: qApplied }), [type, activeOn, qApplied]);
  const products = useLoad(() => get<Product[]>('/products/', { include_unlisted: true }), []);

  const [form, setForm] = useState<FormState | null>(null);
  const [formError, setFormError] = useState<unknown>(null);
  const [saving, setSaving] = useState(false);
  const [productFilter, setProductFilter] = useState('');
  const [deleting, setDeleting] = useState<Discount | null>(null);
  const [deleteError, setDeleteError] = useState<unknown>(null);

  const patchForm = (p: Partial<FormState>) => setForm((f) => (f ? { ...f, ...p } : f));
  const openCreate = () => { setFormError(null); setProductFilter(''); setForm(newForm()); };
  const openEdit = (d: Discount) => { setFormError(null); setProductFilter(''); setForm(fromDiscount(d)); };

  const filteredProducts = useMemo(() => {
    const kw = productFilter.trim().toLowerCase();
    const all = products.data ?? [];
    return kw ? all.filter((p) => p.name.toLowerCase().includes(kw) || p.store_name.toLowerCase().includes(kw)) : all;
  }, [products.data, productFilter]);

  const save = async () => {
    if (!form) return;
    setSaving(true);
    setFormError(null);
    try {
      const body = toInput(form);
      if (form.code == null) {
        const d = await post<Discount>('/discounts/', body);
        toast.success(`已建立折扣，系統產生代碼 ${d.discount_code}`);
      } else {
        await put<Discount>(`/discounts/${form.code}`, body);
        toast.success(`折扣 ${form.code} 已更新`);
      }
      setForm(null);
      list.reload();
    } catch (e) {
      setFormError(e);
      toast.error(e, e instanceof ApiError && e.status === 409 ? '違反商業規則' : undefined);
    } finally {
      setSaving(false);
    }
  };

  const doDelete = async () => {
    if (!deleting) return;
    setSaving(true);
    setDeleteError(null);
    try {
      await del(`/discounts/${deleting.discount_code}`);
      toast.success(`折扣 ${deleting.discount_code} 已刪除`);
      setDeleting(null);
      list.reload();
    } catch (e) {
      setDeleteError(e);
      toast.error(e);
    } finally {
      setSaving(false);
    }
  };

  const deactivate = async (d: Discount) => {
    setSaving(true);
    try {
      const f = fromDiscount(d);
      f.is_active = false;
      await put<Discount>(`/discounts/${d.discount_code}`, toInput(f));
      toast.success(`折扣 ${d.discount_code} 已停用`);
      setDeleting(null);
      list.reload();
    } catch (e) {
      setDeleteError(e);
      toast.error(e);
    } finally {
      setSaving(false);
    }
  };

  const showRate = form && (form.discount_type === 'seasonal' || (form.discount_type === 'special_event' && form.eventMode === 'rate'));
  const pctNum = form ? Number(form.pct) : NaN;

  return (
    <>
      <PageHeader
        title="折扣管理"
        subtitle="運費折扣、季節性折扣、特殊活動折扣；折扣代碼由系統產生且不可修改（BR-18）"
        actions={<button className="bo-btn" onClick={openCreate}>＋ 新增折扣</button>}
      />
      <Card>
        <form className="bo-toolbar" onSubmit={(e) => { e.preventDefault(); setQApplied(q.trim()); }}>
          <Field label="類型">
            <select className="bo-select" value={type} onChange={(e) => setType(e.target.value)}>
              <option value="">全部類型</option>
              {TYPES.map((t) => <option key={t} value={t}>{DISCOUNT_TYPE_LABEL[t]}</option>)}
            </select>
          </Field>
          <Field label="有效日期（含當日）">
            <input type="date" className="bo-input" value={activeOn} onChange={(e) => setActiveOn(e.target.value)} />
          </Field>
          <Field label="關鍵字">
            <input className="bo-input" placeholder="代碼或說明" value={q} onChange={(e) => setQ(e.target.value)} />
          </Field>
          <button className="bo-btn bo-btn--ghost" type="submit">搜尋</button>
          <button type="button" className="bo-btn bo-btn--ghost" onClick={() => setActiveOn(isoDate())}>今天有效</button>
          {(type || activeOn || qApplied) && (
            <button type="button" className="bo-btn bo-btn--ghost" onClick={() => { setType(''); setActiveOn(''); setQ(''); setQApplied(''); }}>清除</button>
          )}
        </form>
        <ErrorAlert error={list.error} />
        {list.loading && !list.data ? <Loading /> : !list.data || list.data.length === 0 ? <Empty>沒有折扣政策</Empty> : (
          <div className="bo-table-wrap">
            <table className="bo-table">
              <thead>
                <tr><th>代碼</th><th>類型</th><th>說明</th><th>規則</th><th>期間</th><th>適用商品</th><th className="num">已使用</th><th>狀態</th><th>操作</th></tr>
              </thead>
              <tbody>
                {list.data.map((d) => (
                  <tr key={d.discount_code} className={d.is_active ? '' : 'is-dim'}>
                    <td className="bo-cell-main">{d.discount_code}</td>
                    <td><Badge tone={TYPE_TONE[d.discount_type]}>{DISCOUNT_TYPE_LABEL[d.discount_type]}</Badge></td>
                    <td>{d.description}</td>
                    <td style={{ whiteSpace: 'nowrap' }}>{describeRule(d)}</td>
                    <td style={{ whiteSpace: 'nowrap' }}>{formatDate(d.start_date)} ～ {formatDate(d.end_date)}</td>
                    <td>
                      {d.discount_type !== 'special_event' ? <span className="bo-muted">整筆訂單</span> : d.products.length === 0 ? <span className="bo-muted">—</span> : (
                        <span title={d.products.map((p) => p.name).join('、')}>
                          {d.products.slice(0, 2).map((p) => p.name).join('、')}{d.products.length > 2 ? ` 等 ${d.products.length} 項` : ''}
                        </span>
                      )}
                    </td>
                    <td className="num">{d.used_count}</td>
                    <td>
                      {!d.is_active ? <Badge>停用</Badge> : d.is_current ? <Badge tone="green">進行中</Badge> : <Badge tone="amber">非期間內</Badge>}
                    </td>
                    <td>
                      <div className="bo-btn-row">
                        <button className="bo-btn bo-btn--ghost bo-btn--sm" onClick={() => openEdit(d)}>編輯</button>
                        <button className="bo-btn bo-btn--danger bo-btn--sm" onClick={() => { setDeleteError(null); setDeleting(d); }}>刪除</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {form && (
        <Modal
          wide
          title={form.code ? `編輯折扣 ${form.code}` : '新增折扣'}
          onClose={() => setForm(null)}
          onSubmit={save}
          footer={
            <>
              <button type="button" className="bo-btn bo-btn--ghost" onClick={() => setForm(null)}>取消</button>
              <button type="submit" className="bo-btn" disabled={saving}>{saving ? '儲存中…' : '儲存'}</button>
            </>
          }
        >
          <ErrorAlert error={formError} />
          <div className="bo-form-grid">
            <Field label="折扣代碼" hint="由系統依類型自動產生，建立後不可修改（BR-18）">
              <input className="bo-input" readOnly value={form.code ?? `${CODE_PREFIX[form.discount_type]}-xxxx（儲存後產生）`} />
            </Field>
            <Field label="折扣類型" required hint={form.code ? '類型建立後不可修改' : undefined}>
              <select className="bo-select" value={form.discount_type} disabled={!!form.code} onChange={(e) => patchForm({ discount_type: e.target.value as DiscountType })}>
                {TYPES.map((t) => <option key={t} value={t}>{DISCOUNT_TYPE_LABEL[t]}</option>)}
              </select>
            </Field>
            <Field label="說明" required className="span-2">
              <input className="bo-input" value={form.description} onChange={(e) => patchForm({ description: e.target.value })} placeholder="例如：週年慶全館 95 折" />
            </Field>
            <Field label="開始日期" required>
              <input type="date" className="bo-input" value={form.start_date} onChange={(e) => patchForm({ start_date: e.target.value })} />
            </Field>
            <Field label="結束日期" required hint="開始日須 ≤ 結束日，含首尾兩日（BR-14）">
              <input type="date" className="bo-input" value={form.end_date} onChange={(e) => patchForm({ end_date: e.target.value })} />
            </Field>

            {form.discount_type === 'shipping' && (
              <Field label="免運門檻金額（新台幣元）" required className="span-2" hint="訂單（折扣後）金額達到門檻即免運費；門檻須大於 0（BR-17）">
                <input type="number" className="bo-input" value={form.min_amount} onChange={(e) => patchForm({ min_amount: e.target.value })} />
              </Field>
            )}

            {form.discount_type === 'special_event' && (
              <div className="bo-field span-2">
                <span className="bo-field__label">折扣規則<span className="req">*</span>（擇一，BR-17）</span>
                <div className="bo-checks">
                  <label className="bo-check"><input type="radio" checked={form.eventMode === 'rate'} onChange={() => patchForm({ eventMode: 'rate' })} />折扣率</label>
                  <label className="bo-check"><input type="radio" checked={form.eventMode === 'bxgy'} onChange={() => patchForm({ eventMode: 'bxgy' })} />買 X 送 Y</label>
                </div>
              </div>
            )}

            {showRate && (
              <Field
                label="折抵百分比（%）"
                required
                className="span-2"
                hint={
                  <>輸入「折抵」的百分比，例如輸入 <b>5</b> 代表折抵 5%（打 95 折），系統儲存為 rate = 0.05（BR-15，須介於 0 與 1 之間）
                    {Number.isFinite(pctNum) && form.pct !== '' && <> → 目前：rate = <b>{Math.round(pctNum * 100) / 10000}</b></>}
                  </>
                }
              >
                <input type="number" step="0.01" className="bo-input" value={form.pct} onChange={(e) => patchForm({ pct: e.target.value })} placeholder="5" />
              </Field>
            )}

            {form.discount_type === 'special_event' && form.eventMode === 'bxgy' && (
              <>
                <Field label="買 X 件" required hint="正整數（BR-16）">
                  <input type="number" className="bo-input" value={form.buy_qty} onChange={(e) => patchForm({ buy_qty: e.target.value })} />
                </Field>
                <Field label="送 Y 件" required hint={form.buy_qty && form.free_qty ? `每買 ${Number(form.buy_qty) + Number(form.free_qty)} 件只付 ${form.buy_qty} 件` : '正整數'}>
                  <input type="number" className="bo-input" value={form.free_qty} onChange={(e) => patchForm({ free_qty: e.target.value })} />
                </Field>
              </>
            )}

            {form.discount_type === 'special_event' && (
              <div className="bo-field span-2">
                <span className="bo-field__label">適用商品（已選 {form.product_ids.length} 項）</span>
                <input className="bo-input" placeholder="篩選商品名稱或商店" value={productFilter} onChange={(e) => setProductFilter(e.target.value)} style={{ marginBottom: 6 }} />
                <div className="bo-multi">
                  {products.loading && !products.data ? <span className="bo-muted">載入中…</span> : filteredProducts.map((p) => (
                    <label key={p.product_id}>
                      <input
                        type="checkbox"
                        checked={form.product_ids.includes(p.product_id)}
                        onChange={(e) => patchForm({
                          product_ids: e.target.checked ? [...form.product_ids, p.product_id] : form.product_ids.filter((x) => x !== p.product_id),
                        })}
                      />
                      <span>{p.name}</span>
                      <span className="bo-muted" style={{ fontSize: 12 }}>· {p.store_name}{p.event_discount && p.event_discount.discount_code !== form.code ? ` · 已有活動 ${p.event_discount.discount_code}` : ''}{p.is_listed ? '' : ' · 下架'}</span>
                    </label>
                  ))}
                </div>
                <span className="bo-field__hint">同一商品的特殊活動折扣期間不得重疊（BR-13）；重疊時系統會拒絕並列出衝突的折扣代碼。</span>
              </div>
            )}

            <div className="bo-field span-2">
              <label className="bo-check">
                <input type="checkbox" checked={form.is_active} onChange={(e) => patchForm({ is_active: e.target.checked })} />
                啟用
              </label>
            </div>
          </div>
        </Modal>
      )}

      {deleting && (
        <Modal
          title={`刪除折扣 ${deleting.discount_code}`}
          onClose={() => setDeleting(null)}
          footer={
            <>
              <button type="button" className="bo-btn bo-btn--ghost" onClick={() => setDeleting(null)}>取消</button>
              {(deleteError || deleting.used_count > 0) && deleting.is_active && (
                <button type="button" className="bo-btn bo-btn--ghost" disabled={saving} onClick={() => deactivate(deleting)}>改為停用</button>
              )}
              <button type="button" className="bo-btn bo-btn--danger" disabled={saving} onClick={doDelete}>刪除</button>
            </>
          }
        >
          <ErrorAlert error={deleteError} />
          <p>確定要刪除折扣「{deleting.description}」嗎？</p>
          {deleting.used_count > 0 && <Alert kind="warn">此折扣已被 {deleting.used_count} 筆訂單使用，依 BR-20 不可刪除，建議改為「停用」。</Alert>}
          {!!deleteError && <Alert>已被訂單使用的折扣政策只能停用，請按「改為停用」。</Alert>}
        </Modal>
      )}
    </>
  );
}
