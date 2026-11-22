// PMS-F-004～007：工作人員新增、修改、刪除（或下架）商品，維護庫存
import { useMemo, useState } from 'react';
import { del, formatMoney, get, post, put } from '../../api/client';
import type { Product, ProductInput, Store } from '../../api/types';
import {
  Alert, Badge, Card, ConfirmModal, Empty, ErrorAlert, Field, Loading, Modal, PageHeader, useLoad, useToast,
} from '../../components/Backoffice';

export const CATEGORY_LABEL: Record<string, string> = {
  food: '食品', toy: '玩具', accessory: '配件', care: '清潔保養', home: '居家',
};
const CATEGORIES = Object.keys(CATEGORY_LABEL);
const BUILTIN_IMAGES = ['ball', 'bow', 'brush', 'cage', 'can', 'collar', 'hat', 'dog'].map((n) => `/images/${n}.webp`);
const FALLBACK_IMG = '/images/shop_item.webp';

const emptyForm = (storeId: number): ProductInput => ({
  store_id: storeId, name: '', description: '', category: 'food', image_url: '', price: 0, stock: 0, is_listed: true,
});

export default function ProductsPage() {
  const toast = useToast();
  const [q, setQ] = useState('');
  const [qApplied, setQApplied] = useState('');
  const [storeId, setStoreId] = useState('');
  const [category, setCategory] = useState('');
  const [listed, setListed] = useState<'all' | 'listed' | 'unlisted'>('all');

  const stores = useLoad(() => get<Store[]>('/stores/'), []);
  const products = useLoad(
    () => get<Product[]>('/products/', { q: qApplied, store_id: storeId, category, include_unlisted: true }),
    [qApplied, storeId, category],
  );

  const [editing, setEditing] = useState<{ id: number | null; form: ProductInput } | null>(null);
  const [formError, setFormError] = useState<unknown>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<Product | null>(null);

  const rows = useMemo(
    () => (products.data ?? []).filter((p) => listed === 'all' || (listed === 'listed' ? p.is_listed : !p.is_listed)),
    [products.data, listed],
  );
  const imageChoices = useMemo(() => {
    const set = new Set<string>(BUILTIN_IMAGES);
    (products.data ?? []).forEach((p) => p.image_url && set.add(p.image_url));
    return Array.from(set);
  }, [products.data]);

  const openCreate = () => {
    setFormError(null);
    setEditing({ id: null, form: emptyForm(stores.data?.[0]?.store_id ?? 0) });
  };
  const openEdit = (p: Product) => {
    setFormError(null);
    setEditing({
      id: p.product_id,
      form: {
        store_id: p.store_id, name: p.name, description: p.description ?? '', category: p.category ?? 'food',
        image_url: p.image_url ?? '', price: p.price, stock: p.stock, is_listed: p.is_listed,
      },
    });
  };
  const setForm = (patch: Partial<ProductInput>) => setEditing((e) => (e ? { ...e, form: { ...e.form, ...patch } } : e));

  const save = async () => {
    if (!editing) return;
    setSaving(true);
    setFormError(null);
    try {
      const body = { ...editing.form, price: Number(editing.form.price), stock: Number(editing.form.stock) };
      if (editing.id == null) {
        const p = await post<Product>('/products/', body);
        toast.success(`已新增商品「${p.name}」`);
      } else {
        await put<Product>(`/products/${editing.id}`, body);
        toast.success('商品已更新');
      }
      setEditing(null);
      products.reload();
      stores.reload();
    } catch (e) {
      setFormError(e);
      toast.error(e);
    } finally {
      setSaving(false);
    }
  };

  const doDelete = async () => {
    if (!deleting) return;
    setSaving(true);
    try {
      const res = await del<{ deleted: boolean; unlisted: boolean }>(`/products/${deleting.product_id}`);
      if (res.deleted) toast.success(`「${deleting.name}」已刪除`);
      else toast.info(`「${deleting.name}」已被訂單引用，依 BR-20 不可刪除，已改為下架`, 'BR-20 改為下架');
      setDeleting(null);
      products.reload();
    } catch (e) {
      toast.error(e);
    } finally {
      setSaving(false);
    }
  };

  const toggleListed = async (p: Product) => {
    try {
      await put<Product>(`/products/${p.product_id}`, {
        store_id: p.store_id, name: p.name, description: p.description ?? '', category: p.category ?? '',
        image_url: p.image_url ?? '', price: p.price, stock: p.stock, is_listed: !p.is_listed,
      });
      toast.success(`「${p.name}」已${p.is_listed ? '下架' : '上架'}`);
      products.reload();
    } catch (e) {
      toast.error(e);
    }
  };

  const f = editing?.form;

  return (
    <>
      <PageHeader
        title="商品與庫存"
        subtitle="新增、修改、下架或刪除商品（PMS-F-004～007）；已被訂單引用的商品刪除時會改為下架（BR-20）"
        actions={<button className="bo-btn" onClick={openCreate} disabled={!stores.data?.length}>＋ 新增商品</button>}
      />
      <Card>
        <form className="bo-toolbar" onSubmit={(e) => { e.preventDefault(); setQApplied(q.trim()); }}>
          <Field label="關鍵字">
            <input className="bo-input" placeholder="商品名稱、描述" value={q} onChange={(e) => setQ(e.target.value)} style={{ minWidth: 200 }} />
          </Field>
          <Field label="商店">
            <select className="bo-select" value={storeId} onChange={(e) => setStoreId(e.target.value)}>
              <option value="">全部商店</option>
              {stores.data?.map((s) => <option key={s.store_id} value={s.store_id}>{s.name}</option>)}
            </select>
          </Field>
          <Field label="類別">
            <select className="bo-select" value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">全部類別</option>
              {CATEGORIES.map((c) => <option key={c} value={c}>{CATEGORY_LABEL[c]}</option>)}
            </select>
          </Field>
          <Field label="上架狀態">
            <select className="bo-select" value={listed} onChange={(e) => setListed(e.target.value as typeof listed)}>
              <option value="all">全部</option>
              <option value="listed">上架中</option>
              <option value="unlisted">已下架</option>
            </select>
          </Field>
          <button className="bo-btn bo-btn--ghost" type="submit">搜尋</button>
        </form>
        <ErrorAlert error={products.error} />
        {products.loading && !products.data ? <Loading /> : rows.length === 0 ? <Empty>沒有符合條件的商品</Empty> : (
          <div className="bo-table-wrap">
            <table className="bo-table">
              <thead>
                <tr>
                  <th></th><th>商品</th><th>商店</th><th>類別</th><th className="num">價格</th><th className="num">庫存</th><th>狀態</th><th>操作</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((p) => (
                  <tr key={p.product_id} className={p.is_listed ? '' : 'is-dim'}>
                    <td><img className="bo-thumb" src={p.image_url || FALLBACK_IMG} alt="" onError={(e) => { e.currentTarget.src = FALLBACK_IMG; }} /></td>
                    <td>
                      <div className="bo-cell-main">{p.name}</div>
                      <div className="bo-cell-sub">#{p.product_id}{p.event_discount ? ` · 活動 ${p.event_discount.discount_code}` : ''}</div>
                    </td>
                    <td>{p.store_name}</td>
                    <td>{CATEGORY_LABEL[p.category ?? ''] ?? p.category ?? '—'}</td>
                    <td className="num">{formatMoney(p.price)}</td>
                    <td className="num">
                      {p.stock === 0 ? <Badge tone="red">缺貨</Badge> : p.stock < 10 ? <Badge tone="amber">{p.stock}</Badge> : p.stock}
                    </td>
                    <td>{p.is_listed ? <Badge tone="green">上架</Badge> : <Badge>下架</Badge>}</td>
                    <td>
                      <div className="bo-btn-row">
                        <button className="bo-btn bo-btn--ghost bo-btn--sm" onClick={() => openEdit(p)}>編輯</button>
                        <button className="bo-btn bo-btn--ghost bo-btn--sm" onClick={() => toggleListed(p)}>{p.is_listed ? '下架' : '上架'}</button>
                        <button className="bo-btn bo-btn--danger bo-btn--sm" onClick={() => setDeleting(p)}>刪除</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {products.data && <p className="bo-muted bo-mt">共 {rows.length} 項商品</p>}
      </Card>

      {editing && f && (
        <Modal
          wide
          title={editing.id == null ? '新增商品' : `編輯商品 #${editing.id}`}
          onClose={() => setEditing(null)}
          onSubmit={save}
          footer={
            <>
              <button type="button" className="bo-btn bo-btn--ghost" onClick={() => setEditing(null)}>取消</button>
              <button type="submit" className="bo-btn" disabled={saving}>{saving ? '儲存中…' : '儲存'}</button>
            </>
          }
        >
          <ErrorAlert error={formError} />
          <div className="bo-form-grid">
            <Field label="商店" required>
              <select className="bo-select" value={f.store_id} onChange={(e) => setForm({ store_id: Number(e.target.value) })}>
                {stores.data?.map((s) => <option key={s.store_id} value={s.store_id}>{s.name}</option>)}
              </select>
            </Field>
            <Field label="類別" required>
              <select className="bo-select" value={f.category} onChange={(e) => setForm({ category: e.target.value })}>
                {CATEGORIES.map((c) => <option key={c} value={c}>{CATEGORY_LABEL[c]}（{c}）</option>)}
              </select>
            </Field>
            <Field label="商品名稱" required className="span-2">
              <input className="bo-input" value={f.name} onChange={(e) => setForm({ name: e.target.value })} required />
            </Field>
            <Field label="商品描述" className="span-2">
              <textarea className="bo-textarea" value={f.description} onChange={(e) => setForm({ description: e.target.value })} />
            </Field>
            <Field label="價格（新台幣元）" required hint="整數，不可為負">
              <input type="number" className="bo-input" value={f.price} onChange={(e) => setForm({ price: e.target.value === '' ? 0 : Number(e.target.value) })} />
            </Field>
            <Field label="庫存數量" required hint="不可為負（BR-06）">
              <input type="number" className="bo-input" value={f.stock} onChange={(e) => setForm({ stock: e.target.value === '' ? 0 : Number(e.target.value) })} />
            </Field>
            <div className="bo-field span-2">
              <span className="bo-field__label">商品圖片</span>
              <div className="bo-img-preview">
                <img src={f.image_url || FALLBACK_IMG} alt="預覽" onError={(e) => { e.currentTarget.src = FALLBACK_IMG; }} />
                <div style={{ flex: 1 }}>
                  <input className="bo-input" placeholder="/images/products/xxx.webp" value={f.image_url} onChange={(e) => setForm({ image_url: e.target.value })} />
                  <div className="bo-img-picks">
                    {imageChoices.map((src) => (
                      <button type="button" key={src} title={src} className={f.image_url === src ? 'active' : ''} onClick={() => setForm({ image_url: src })}>
                        <img src={src} alt="" onError={(e) => { e.currentTarget.style.opacity = '0.2'; }} />
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <div className="bo-field span-2">
              <label className="bo-check">
                <input type="checkbox" checked={f.is_listed} onChange={(e) => setForm({ is_listed: e.target.checked })} />
                上架（顧客可在商店看到並購買）
              </label>
            </div>
          </div>
        </Modal>
      )}

      {deleting && (
        <ConfirmModal
          title="刪除商品"
          danger
          busy={saving}
          confirmLabel="刪除"
          onClose={() => setDeleting(null)}
          onConfirm={doDelete}
          message={
            <>
              <p>確定要刪除「<b>{deleting.name}</b>」嗎？</p>
              <Alert>若此商品已出現在訂單中，依 <b>BR-20</b> 系統不會真的刪除，而是改為「下架」以保留歷史訂單資料。</Alert>
            </>
          }
        />
      )}
    </>
  );
}
