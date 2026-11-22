import React from 'react';
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

  return (
    <nav className="navigation-bar">
      <div className="navigation-bar__left">{languageSwitcher}</div>
      <div className="navigation-bar__center">
        <button onClick={() => navigate('/')} className="navigation-bar__logo-button" aria-label={t.nav.home}>
          <img src="/images/fuwa_title.webp" alt="FUWA FUWA Shop" className="navigation-bar__logo" />
        </button>
      </div>
      <div className="navigation-bar__right">
        <button className="navigation-bar__link" onClick={() => navigate('/stores')}>
          🏪 {t.nav.stores}
        </button>
        {isCustomer && (
          <button className="navigation-bar__link" onClick={() => navigate('/my-orders')}>
            📦 {t.nav.myOrders}
          </button>
        )}
        {!user && (
          <button
            className="navigation-bar__btn navigation-bar__btn--login"
            onClick={() => navigate('/login')}
            title={t.nav.login}
          >
            <span>👤</span>
          </button>
        )}
        {(isCustomer || !user) && (
          <button
            className="navigation-bar__btn navigation-bar__btn--cart"
            onClick={() => navigate('/cart')}
            title={t.nav.cart}
          >
            <img src="/images/shopping-cart-icon.webp" alt={t.nav.cart} />
            {itemCount > 0 && <span className="navigation-bar__badge">{itemCount}</span>}
          </button>
        )}
      </div>
    </nav>
  );
};
