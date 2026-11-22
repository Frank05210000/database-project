import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import './RoleSwitcher.css';

/** 同一個網站依登入角色切換三種介面：顧客購物、工作人員管理、平台管理。 */
export const RoleSwitcher = () => {
  const { user, hasRole, logout } = useAuth();
  const navigate = useNavigate();
  if (!user) return null;
  const links = [
    { to: '/', label: '購物', show: true },
    { to: '/staff', label: '工作人員', show: hasRole('staff') },
    { to: '/admin', label: '平台管理', show: hasRole('admin') },
  ].filter((l) => l.show);
  return (
    <div className="role-switcher">
      {links.length > 1 &&
        links.map((l) => (
          <NavLink key={l.to} to={l.to} end={l.to === '/'} className="role-switcher__link">
            {l.label}
          </NavLink>
        ))}
      <span className="role-switcher__user">👤 {user.name}</span>
      <button
        className="role-switcher__logout"
        onClick={() => {
          logout();
          navigate('/');
        }}
      >
        登出
      </button>
    </div>
  );
};
