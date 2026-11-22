// 平台管理介面：使用者帳號（新增、查詢、修改）、角色與權限、停用／啟用帳號
import { Navigate, Route, Routes } from 'react-router-dom';
import { BackofficeLayout, NavItem } from '../../components/Backoffice';
import AdminDashboard from './AdminDashboard';
import UsersPage from './UsersPage';
import StoresPage from './StoresPage';

const NAV: NavItem[] = [
  { to: '/admin', label: '總覽', icon: '🏠', end: true },
  { to: '/admin/users', label: '使用者帳號', icon: '👥' },
  { to: '/admin/stores', label: '商店資料', icon: '🏪' },
];

export default function AdminApp() {
  return (
    <BackofficeLayout title="平台管理介面" tag="平台管理" nav={NAV}>
      <Routes>
        <Route index element={<AdminDashboard />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="stores" element={<StoresPage />} />
        <Route path="*" element={<Navigate to="/admin" replace />} />
      </Routes>
    </BackofficeLayout>
  );
}
