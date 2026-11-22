import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useEffect } from 'react';
import { HomePage } from './pages/HomePage';
import { ProductDetail } from './pages/ProductDetail';
import { CartPage } from './pages/CartPage';
import { LoginPage } from './pages/LoginPage';
import OrderPage from './pages/OrderPage';
import OrderSuccessPage from './pages/OrderSuccessPage';
import MyOrdersPage from './pages/MyOrdersPage';
import OrderDetailPage from './pages/OrderDetailPage';
import StoresPage from './pages/StoresPage';
import StoreDetailPage from './pages/StoreDetailPage';
import { NavigationBar } from './components/Layout/NavigationBar';
import { LanguageProvider } from './i18n';
import { AuthProvider } from './contexts/AuthContext';
import { CartProvider } from './contexts/CartContext';
import { LanguageSwitcher } from './components/Common/LanguageSwitcher';
import { RoleSwitcher } from './components/Common/RoleSwitcher';
import { RequireRole } from './components/Common/RequireRole';
import StaffApp from './pages/staff/StaffApp';
import AdminApp from './pages/admin/AdminApp';
import './assets/styles/globals.css';
import './App.css';
import './assets/styles/customer.css';

function AppContent() {
  const location = useLocation();
  const isBackoffice = location.pathname.startsWith('/staff') || location.pathname.startsWith('/admin');

  useEffect(() => {
    const isProductDetail = location.pathname.startsWith('/product/');
    if (isProductDetail) {
      document.body.classList.add('product-detail-body');
    } else {
      document.body.classList.remove('product-detail-body');
    }
    return () => {
      document.body.classList.remove('product-detail-body');
    };
  }, [location.pathname]);

  // 工作人員與平台管理介面有自己的版面
  if (isBackoffice) {
    return (
      <Routes>
        <Route path="/staff/*" element={<RequireRole role="staff"><StaffApp /></RequireRole>} />
        <Route path="/admin/*" element={<RequireRole role="admin"><AdminApp /></RequireRole>} />
      </Routes>
    );
  }

  return (
    <div className="app app-body">
      {/* Navigation Bar */}
      <NavigationBar
        languageSwitcher={
          <>
            <LanguageSwitcher />
            <RoleSwitcher />
          </>
        }
      />

      {/* Routes */}
      <main className="app__content">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/product/:id" element={<ProductDetail />} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/order" element={<OrderPage />} />
          <Route path="/order-success/:orderId" element={<OrderSuccessPage />} />
          <Route path="/my-orders" element={<MyOrdersPage />} />
          <Route path="/order/:orderId" element={<OrderDetailPage />} />
          <Route path="/stores" element={<StoresPage />} />
          <Route path="/stores/:id" element={<StoreDetailPage />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <CartProvider>
          <Router>
            <AppContent />
          </Router>
        </CartProvider>
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;
