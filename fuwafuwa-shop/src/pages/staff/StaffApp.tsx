// 工作人員管理介面：商品與庫存、訂單、退貨、折扣、報表
import { Navigate, Route, Routes } from 'react-router-dom';
import { BackofficeLayout, NavItem } from '../../components/Backoffice';
import StaffDashboard from './StaffDashboard';
import ProductsPage from './ProductsPage';
import OrdersPage from './OrdersPage';
import OrderDetailPage from './OrderDetailPage';
import ReturnsPage from './ReturnsPage';
import DiscountsPage from './DiscountsPage';
import ReportsPage from './ReportsPage';

const NAV: NavItem[] = [
  { to: '/staff', label: '總覽', icon: '🏠', end: true },
  { to: '/staff/products', label: '商品與庫存', icon: '📦' },
  { to: '/staff/orders', label: '訂單管理', icon: '🧾' },
  { to: '/staff/returns', label: '退貨審核', icon: '↩️' },
  { to: '/staff/discounts', label: '折扣管理', icon: '🏷️' },
  { to: '/staff/reports', label: '銷售報表', icon: '📊' },
];

export default function StaffApp() {
  return (
    <BackofficeLayout title="工作人員管理介面" tag="工作人員" nav={NAV}>
      <Routes>
        <Route index element={<StaffDashboard />} />
        <Route path="products" element={<ProductsPage />} />
        <Route path="orders" element={<OrdersPage />} />
        <Route path="orders/:id" element={<OrderDetailPage />} />
        <Route path="returns" element={<ReturnsPage />} />
        <Route path="returns/:id" element={<ReturnsPage />} />
        <Route path="discounts" element={<DiscountsPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="*" element={<Navigate to="/staff" replace />} />
      </Routes>
    </BackofficeLayout>
  );
}
