import { Link } from 'react-router-dom';
import { get } from '../../api/client';
import type { AdminStats } from '../../api/types';
import { Card, ErrorAlert, KpiCard, Loading, PageHeader, useLoad } from '../../components/Backoffice';
import { useAuth } from '../../contexts/AuthContext';

export default function AdminDashboard() {
  const { user } = useAuth();
  const { data, loading, error } = useLoad(() => get<AdminStats>('/admin/stats'), []);

  return (
    <>
      <PageHeader title={`你好，${user?.name ?? ''}`} subtitle="平台帳號與角色概況" />
      <ErrorAlert error={error} />
      {loading && !data ? <Loading /> : data && (
        <div className="bo-grid bo-grid--kpi">
          <KpiCard label="使用者總數" value={data.users} icon="👥" />
          <KpiCard label="顧客" value={data.customers} icon="🐾" accent="#e3eef9" />
          <KpiCard label="工作人員" value={data.staff} icon="🧑‍🔧" accent="#fdf1d8" />
          <KpiCard label="平台管理員" value={data.admins} icon="🛡️" accent="#fbe6de" hint="系統至少保留一位啟用中的管理員" />
          <KpiCard label="停用帳號" value={data.inactive} icon="⛔" accent="#f1ebe7" />
        </div>
      )}
      <Card title="快速前往">
        <div className="bo-quick">
          <Link to="/admin/users">👥 管理使用者帳號</Link>
          <Link to="/admin/users?is_active=false">⛔ 已停用帳號</Link>
          <Link to="/admin/users?role=staff">🧑‍🔧 工作人員名單</Link>
          <Link to="/admin/stores">🏪 商店資料</Link>
        </div>
      </Card>
      <Card title="平台管理員職責">
        <ul style={{ margin: 0, paddingLeft: 20, lineHeight: 1.9 }}>
          <li>管理使用者帳號：新增、查詢、修改</li>
          <li>管理角色與權限：指派或移除 customer（顧客）、staff（工作人員）、admin（平台管理員）</li>
          <li>停用或啟用帳號（停用的帳號無法登入）</li>
          <li>管理員不能停用自己或移除自己的 admin 角色；系統至少保留一位啟用中的管理員</li>
        </ul>
      </Card>
    </>
  );
}
