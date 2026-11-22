// STS：平台管理員檢視與修改商店資料
import { useState } from 'react';
import { get, put } from '../../api/client';
import type { Store } from '../../api/types';
import { Card, Empty, ErrorAlert, Field, Loading, Modal, PageHeader, useLoad, useToast } from '../../components/Backoffice';

interface StoreForm { name: string; address: string; email: string; phone: string }

export default function StoresPage() {
  const toast = useToast();
  const stores = useLoad(() => get<Store[]>('/stores/'), []);
  const [editing, setEditing] = useState<{ id: number; form: StoreForm } | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const save = async () => {
    if (!editing) return;
    setBusy(true);
    setError(null);
    try {
      const s = await put<Store>(`/stores/${editing.id}`, editing.form);
      toast.success(`商店「${s.name}」已更新`);
      setEditing(null);
      stores.reload();
    } catch (e) {
      setError(e);
      toast.error(e);
    } finally {
      setBusy(false);
    }
  };

  const setForm = (p: Partial<StoreForm>) => setEditing((e) => (e ? { ...e, form: { ...e.form, ...p } } : e));

  return (
    <>
      <PageHeader title="商店資料" subtitle="檢視各商店與評價，修改聯絡資訊" />
      <Card>
        <ErrorAlert error={stores.error} />
        {stores.loading && !stores.data ? <Loading /> : !stores.data || stores.data.length === 0 ? <Empty>沒有商店</Empty> : (
          <div className="bo-table-wrap">
            <table className="bo-table">
              <thead><tr><th>#</th><th>商店名稱</th><th>地址</th><th>Email</th><th>電話</th><th className="num">商品數</th><th className="num">評分</th><th>操作</th></tr></thead>
              <tbody>
                {stores.data.map((s) => (
                  <tr key={s.store_id}>
                    <td>{s.store_id}</td>
                    <td className="bo-cell-main">{s.name}</td>
                    <td>{s.address}</td>
                    <td>{s.email}</td>
                    <td>{s.phone}</td>
                    <td className="num">{s.product_count}</td>
                    <td className="num">{s.avg_rating != null ? `★ ${Number(s.avg_rating).toFixed(1)}（${s.review_count}）` : '—'}</td>
                    <td>
                      <button className="bo-btn bo-btn--ghost bo-btn--sm" onClick={() => { setError(null); setEditing({ id: s.store_id, form: { name: s.name, address: s.address, email: s.email, phone: s.phone } }); }}>編輯</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {editing && (
        <Modal
          title={`編輯商店 #${editing.id}`}
          onClose={() => setEditing(null)}
          onSubmit={save}
          footer={
            <>
              <button type="button" className="bo-btn bo-btn--ghost" onClick={() => setEditing(null)}>取消</button>
              <button type="submit" className="bo-btn" disabled={busy}>儲存</button>
            </>
          }
        >
          <ErrorAlert error={error} />
          <Field label="商店名稱" required><input className="bo-input" value={editing.form.name} onChange={(e) => setForm({ name: e.target.value })} /></Field>
          <Field label="地址" required><input className="bo-input" value={editing.form.address} onChange={(e) => setForm({ address: e.target.value })} /></Field>
          <Field label="Email" required><input type="email" className="bo-input" value={editing.form.email} onChange={(e) => setForm({ email: e.target.value })} /></Field>
          <Field label="電話" required><input className="bo-input" value={editing.form.phone} onChange={(e) => setForm({ phone: e.target.value })} /></Field>
        </Modal>
      )}
    </>
  );
}
