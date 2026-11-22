// AAS：平台管理員管理使用者帳號、角色與啟用狀態
import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { formatDateTime, get, patch, post, put, ROLE_LABEL } from '../../api/client';
import type { Role, User } from '../../api/types';
import {
  Alert, Badge, Card, ConfirmModal, Empty, ErrorAlert, Field, Loading, Modal, PageHeader, RoleChip, useLoad, useToast,
} from '../../components/Backoffice';
import { useAuth } from '../../contexts/AuthContext';

const ROLES: Role[] = ['customer', 'staff', 'admin'];

interface UserForm {
  loginid: string; name: string; password: string; email: string; address: string; phone: string; roles: Role[];
}
const blankForm = (): UserForm => ({ loginid: '', name: '', password: '', email: '', address: '', phone: '', roles: ['customer'] });

const RoleChecks = ({ value, onChange }: { value: Role[]; onChange: (r: Role[]) => void }) => (
  <div className="bo-checks">
    {ROLES.map((r) => (
      <label key={r} className="bo-check">
        <input type="checkbox" checked={value.includes(r)} onChange={(e) => onChange(e.target.checked ? [...value, r] : value.filter((x) => x !== r))} />
        {ROLE_LABEL[r]}（{r}）
      </label>
    ))}
  </div>
);

export default function UsersPage() {
  const toast = useToast();
  const { user: me, refresh } = useAuth();
  const [params, setParams] = useSearchParams();
  const role = params.get('role') ?? '';
  const isActive = params.get('is_active') ?? '';
  const qApplied = params.get('q') ?? '';
  const [q, setQ] = useState(qApplied);

  const setParam = (k: string, v: string) => {
    const next = new URLSearchParams(params);
    if (v) next.set(k, v); else next.delete(k);
    setParams(next, { replace: true });
  };

  const users = useLoad(() => get<User[]>('/admin/users', { q: qApplied, role, is_active: isActive }), [qApplied, role, isActive]);

  const [creating, setCreating] = useState<UserForm | null>(null);
  const [editing, setEditing] = useState<{ user: User; form: UserForm } | null>(null);
  const [rolesFor, setRolesFor] = useState<{ user: User; roles: Role[] } | null>(null);
  const [toggling, setToggling] = useState<User | null>(null);
  const [modalError, setModalError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const afterChange = async (u: User) => {
    users.reload();
    if (me && u.user_id === me.user_id) await refresh();
  };

  const run = async (fn: () => Promise<void>) => {
    setBusy(true);
    setModalError(null);
    try {
      await fn();
    } catch (e) {
      setModalError(e);
      toast.error(e);
    } finally {
      setBusy(false);
    }
  };

  const opt = (s: string) => (s.trim() === '' ? null : s.trim());

  const submitCreate = () => run(async () => {
    if (!creating) return;
    const u = await post<User>('/admin/users', {
      loginid: creating.loginid.trim(), name: creating.name.trim(), password: creating.password, email: creating.email.trim(),
      address: opt(creating.address), phone: opt(creating.phone), roles: creating.roles,
    });
    toast.success(`已建立帳號 ${u.loginid}`);
    setCreating(null);
    users.reload();
  });

  const submitEdit = () => run(async () => {
    if (!editing) return;
    const f = editing.form;
    const u = await put<User>(`/admin/users/${editing.user.user_id}`, {
      name: f.name.trim(), email: f.email.trim(), address: opt(f.address), phone: opt(f.phone),
      ...(f.password ? { password: f.password } : {}),
    });
    toast.success(`已更新 ${u.loginid} 的資料${f.password ? '（含新密碼）' : ''}`);
    setEditing(null);
    await afterChange(u);
  });

  const submitRoles = () => run(async () => {
    if (!rolesFor) return;
    const u = await put<User>(`/admin/users/${rolesFor.user.user_id}/roles`, { roles: rolesFor.roles });
    toast.success(`${u.loginid} 的角色已更新為：${u.roles.map((r) => ROLE_LABEL[r]).join('、')}`);
    setRolesFor(null);
    await afterChange(u);
  });

  const submitToggle = () => run(async () => {
    if (!toggling) return;
    const u = await patch<User>(`/admin/users/${toggling.user_id}/status`, { is_active: !toggling.is_active });
    toast.success(`帳號 ${u.loginid} 已${u.is_active ? '啟用' : '停用'}`);
    setToggling(null);
    await afterChange(u);
  });

  const isMe = (u: User) => me?.user_id === u.user_id;

  return (
    <>
      <PageHeader
        title="使用者帳號"
        subtitle="新增、查詢、修改帳號；指派或移除角色；停用或啟用帳號"
        actions={<button className="bo-btn" onClick={() => { setModalError(null); setCreating(blankForm()); }}>＋ 新增使用者</button>}
      />
      <Card>
        <form className="bo-toolbar" onSubmit={(e) => { e.preventDefault(); setParam('q', q.trim()); }}>
          <Field label="關鍵字">
            <input className="bo-input" placeholder="帳號、姓名或 Email" value={q} onChange={(e) => setQ(e.target.value)} style={{ minWidth: 220 }} />
          </Field>
          <Field label="角色">
            <select className="bo-select" value={role} onChange={(e) => setParam('role', e.target.value)}>
              <option value="">全部角色</option>
              {ROLES.map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}
            </select>
          </Field>
          <Field label="狀態">
            <select className="bo-select" value={isActive} onChange={(e) => setParam('is_active', e.target.value)}>
              <option value="">全部</option>
              <option value="true">啟用中</option>
              <option value="false">已停用</option>
            </select>
          </Field>
          <button className="bo-btn bo-btn--ghost" type="submit">搜尋</button>
          {(role || isActive || qApplied) && (
            <button type="button" className="bo-btn bo-btn--ghost" onClick={() => { setQ(''); setParams({}, { replace: true }); }}>清除</button>
          )}
        </form>
        <ErrorAlert error={users.error} />
        {users.loading && !users.data ? <Loading /> : !users.data || users.data.length === 0 ? <Empty>找不到使用者</Empty> : (
          <div className="bo-table-wrap">
            <table className="bo-table">
              <thead>
                <tr><th>帳號</th><th>姓名</th><th>Email</th><th>角色</th><th>狀態</th><th>建立時間</th><th>操作</th></tr>
              </thead>
              <tbody>
                {users.data.map((u) => (
                  <tr key={u.user_id} className={u.is_active ? '' : 'is-dim'}>
                    <td className="bo-cell-main" style={{ whiteSpace: 'nowrap' }}>{u.loginid}{isMe(u) && <span className="bo-muted">（你）</span>}</td>
                    <td style={{ whiteSpace: 'nowrap' }}>{u.name}</td>
                    <td>{u.email}</td>
                    <td><div className="bo-chips">{u.roles.map((r) => <RoleChip key={r} role={r} />)}</div></td>
                    <td>{u.is_active ? <Badge tone="green">啟用</Badge> : <Badge tone="red">停用</Badge>}</td>
                    <td style={{ whiteSpace: 'nowrap' }}>{formatDateTime(u.created_at)}</td>
                    <td>
                      <div className="bo-btn-row" style={{ flexWrap: 'nowrap' }}>
                        <button className="bo-btn bo-btn--ghost bo-btn--sm" onClick={() => {
                          setModalError(null);
                          setEditing({ user: u, form: { loginid: u.loginid, name: u.name, password: '', email: u.email, address: u.address ?? '', phone: u.phone ?? '', roles: u.roles } });
                        }}>編輯</button>
                        <button className="bo-btn bo-btn--ghost bo-btn--sm" onClick={() => { setModalError(null); setRolesFor({ user: u, roles: [...u.roles] }); }}>角色</button>
                        <button className={`bo-btn bo-btn--sm ${u.is_active ? 'bo-btn--danger' : 'bo-btn--success'}`} onClick={() => { setModalError(null); setToggling(u); }}>
                          {u.is_active ? '停用' : '啟用'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {users.data && <p className="bo-muted bo-mt">共 {users.data.length} 位使用者</p>}
      </Card>

      {creating && (
        <Modal
          wide
          title="新增使用者"
          onClose={() => setCreating(null)}
          onSubmit={submitCreate}
          footer={
            <>
              <button type="button" className="bo-btn bo-btn--ghost" onClick={() => setCreating(null)}>取消</button>
              <button type="submit" className="bo-btn" disabled={busy}>建立帳號</button>
            </>
          }
        >
          <ErrorAlert error={modalError} />
          <div className="bo-form-grid">
            <Field label="登入帳號" required><input className="bo-input" value={creating.loginid} onChange={(e) => setCreating({ ...creating, loginid: e.target.value })} autoComplete="off" /></Field>
            <Field label="姓名" required><input className="bo-input" value={creating.name} onChange={(e) => setCreating({ ...creating, name: e.target.value })} /></Field>
            <Field label="密碼" required><input type="password" className="bo-input" value={creating.password} onChange={(e) => setCreating({ ...creating, password: e.target.value })} autoComplete="new-password" /></Field>
            <Field label="Email" required><input type="email" className="bo-input" value={creating.email} onChange={(e) => setCreating({ ...creating, email: e.target.value })} /></Field>
            <Field label="地址" className="span-2"><input className="bo-input" value={creating.address} onChange={(e) => setCreating({ ...creating, address: e.target.value })} /></Field>
            <Field label="電話"><input className="bo-input" value={creating.phone} onChange={(e) => setCreating({ ...creating, phone: e.target.value })} /></Field>
            <div className="bo-field span-2">
              <span className="bo-field__label">角色<span className="req">*</span>（至少一個）</span>
              <RoleChecks value={creating.roles} onChange={(roles) => setCreating({ ...creating, roles })} />
            </div>
          </div>
        </Modal>
      )}

      {editing && (
        <Modal
          wide
          title={`編輯使用者：${editing.user.loginid}`}
          onClose={() => setEditing(null)}
          onSubmit={submitEdit}
          footer={
            <>
              <button type="button" className="bo-btn bo-btn--ghost" onClick={() => setEditing(null)}>取消</button>
              <button type="submit" className="bo-btn" disabled={busy}>儲存</button>
            </>
          }
        >
          <ErrorAlert error={modalError} />
          <div className="bo-form-grid">
            <Field label="登入帳號" hint="帳號建立後不可修改"><input className="bo-input" readOnly value={editing.form.loginid} /></Field>
            <Field label="姓名" required><input className="bo-input" value={editing.form.name} onChange={(e) => setEditing({ ...editing, form: { ...editing.form, name: e.target.value } })} /></Field>
            <Field label="Email" required><input type="email" className="bo-input" value={editing.form.email} onChange={(e) => setEditing({ ...editing, form: { ...editing.form, email: e.target.value } })} /></Field>
            <Field label="電話"><input className="bo-input" value={editing.form.phone} onChange={(e) => setEditing({ ...editing, form: { ...editing.form, phone: e.target.value } })} /></Field>
            <Field label="地址" className="span-2"><input className="bo-input" value={editing.form.address} onChange={(e) => setEditing({ ...editing, form: { ...editing.form, address: e.target.value } })} /></Field>
            <Field label="新密碼" className="span-2" hint="留空表示不變更密碼">
              <input type="password" className="bo-input" value={editing.form.password} onChange={(e) => setEditing({ ...editing, form: { ...editing.form, password: e.target.value } })} autoComplete="new-password" />
            </Field>
          </div>
          <p className="bo-muted" style={{ fontSize: 12, margin: 0 }}>角色與啟用狀態請用列表上的「角色」「停用／啟用」按鈕調整。</p>
        </Modal>
      )}

      {rolesFor && (
        <Modal
          title={`角色與權限：${rolesFor.user.loginid}`}
          onClose={() => setRolesFor(null)}
          onSubmit={submitRoles}
          footer={
            <>
              <button type="button" className="bo-btn bo-btn--ghost" onClick={() => setRolesFor(null)}>取消</button>
              <button type="submit" className="bo-btn" disabled={busy}>儲存角色</button>
            </>
          }
        >
          <ErrorAlert error={modalError} />
          <p style={{ marginTop: 0 }}>勾選要指派給 <b>{rolesFor.user.name}</b> 的角色（整組取代，至少保留一個）：</p>
          <RoleChecks value={rolesFor.roles} onChange={(roles) => setRolesFor({ ...rolesFor, roles })} />
          <ul className="bo-muted" style={{ fontSize: 12, paddingLeft: 18, marginBottom: 0 }}>
            <li>顧客：購物、下單、申請退貨</li>
            <li>工作人員：管理商品、訂單、退貨、折扣與報表</li>
            <li>平台管理員：管理使用者帳號與角色</li>
          </ul>
          {isMe(rolesFor.user) && !rolesFor.roles.includes('admin') && (
            <Alert kind="warn">你正在移除自己的平台管理員角色，系統會拒絕此操作。</Alert>
          )}
        </Modal>
      )}

      {toggling && (
        <ConfirmModal
          title={toggling.is_active ? '停用帳號' : '啟用帳號'}
          danger={toggling.is_active}
          busy={busy}
          confirmLabel={toggling.is_active ? '停用' : '啟用'}
          onClose={() => setToggling(null)}
          onConfirm={submitToggle}
          message={
            <>
              <ErrorAlert error={modalError} />
              <p>
                確定要{toggling.is_active ? '停用' : '啟用'}帳號 <b>{toggling.loginid}</b>（{toggling.name}）嗎？
                {toggling.is_active && '停用後該使用者將無法登入。'}
              </p>
              {toggling.is_active && isMe(toggling) && <Alert kind="warn">這是你自己的帳號，系統會拒絕停用。</Alert>}
            </>
          }
        />
      )}
    </>
  );
}
