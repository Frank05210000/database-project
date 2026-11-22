import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useCart } from '../../hooks/useCart';
import { useLanguage } from '../../i18n';
import './NavigationBar.css';

interface NavigationBarProps {
  /** 左側欄位（語言切換、角色切換由 App.tsx 注入） */
  languageSwitcher?: React.ReactNode;
}

export const NavigationBar: React.FC<NavigationBarProps> = ({ languageSwitcher }) => {
  const navigate = useNavigate();
  const { user, hasRole } = useAuth();
  const { itemCount } = useCart();
  const { t } = useLanguage();
  const isCustomer = !!user && hasRole('customer');
  const [menuOpen, setMenuOpen] = useState(false);

  const handleNav = (path: string) => {
    setMenuOpen(false);
    navigate(path);
  };

  return (
    <nav className="navigation-bar">
      <div className="navigation-bar__main">
        {/* 左側：桌面版語言與角色切換 */}
        <div className="navigation-bar__left">{languageSwitcher}</div>

        {/* 中間：Logo */}
        <div className="navigation-bar__center">
          <button onClick={() => handleNav('/')} className="navigation-bar__logo-button" aria-label={t.nav.home}>
            <img src="/images/fuwa_title.webp" alt="FUWA FUWA Shop" className="navigation-bar__logo" />
          </button>
        </div>

        {/* 右側：桌面版導覽連結與按鈕 */}
        <div className="navigation-bar__right">
          <button className="navigation-bar__link" onClick={() => handleNav('/stores')}>
            🏪 {t.nav.stores}
          </button>
          {isCustomer && (
            <button className="navigation-bar__link" onClick={() => handleNav('/my-orders')}>
              📦 {t.nav.myOrders}
            </button>
          )}
          {!user && (
            <button
              className="navigation-bar__btn navigation-bar__btn--login"
              onClick={() => handleNav('/login')}
              title={t.nav.login}
            >
              <span>👤</span>
            </button>
          )}
          {(isCustomer || !user) && (
            <button
              className="navigation-bar__btn navigation-bar__btn--cart"
              onClick={() => handleNav('/cart')}
              title={t.nav.cart}
            >
              <img src="/images/shopping-cart-icon.webp" alt={t.nav.cart} />
              {itemCount > 0 && <span className="navigation-bar__badge">{itemCount}</span>}
            </button>
          )}
        </div>

        {/* 手機版頂端右側控制：購物車與折疊選單按鈕 */}
        <div className="navigation-bar__mobile-controls">
          {(isCustomer || !user) && (
            <button
              className="navigation-bar__btn navigation-bar__btn--cart navigation-bar__btn--mobile-cart"
              onClick={() => handleNav('/cart')}
              title={t.nav.cart}
            >
              <img src="/images/shopping-cart-icon.webp" alt={t.nav.cart} />
              {itemCount > 0 && <span className="navigation-bar__badge">{itemCount}</span>}
            </button>
          )}
          <button
            className="navigation-bar__toggle-btn"
            onClick={() => setMenuOpen((prev) => !prev)}
            aria-label="Toggle navigation menu"
            aria-expanded={menuOpen}
          >
            {menuOpen ? '✕' : '☰'}
          </button>
        </div>
      </div>

      {/* 手機版折疊選單 */}
      {menuOpen && (
        <div className="navigation-bar__mobile-drawer">
          <div className="navigation-bar__mobile-links">
            <button className="navigation-bar__drawer-link" onClick={() => handleNav('/stores')}>
              🏪 {t.nav.stores}
            </button>
            {isCustomer && (
              <button className="navigation-bar__drawer-link" onClick={() => handleNav('/my-orders')}>
                📦 {t.nav.myOrders}
              </button>
            )}
            {!user && (
              <button className="navigation-bar__drawer-link" onClick={() => handleNav('/login')}>
                👤 {t.nav.login}
              </button>
            )}
          </div>
          <div className="navigation-bar__mobile-switchers">
            {languageSwitcher}
          </div>
        </div>
      )}
    </nav>
  );
};
