import { ReactNode } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { RoleSwitcher } from '../Common/RoleSwitcher';
import { ToastProvider } from './Toast';
import './Backoffice.css';

export interface NavItem { to: string; label: string; icon: string; end?: boolean }

/** 後台共用版面：左側選單＋上方標題列（含角色切換） */
export const BackofficeLayout = ({ title, tag, nav, children }: { title: string; tag: string; nav: NavItem[]; children: ReactNode }) => (
  <ToastProvider>
    <div className="bo">
      <aside className="bo-sidebar">
        <Link to={nav[0]?.to ?? '/'} className="bo-sidebar__brand">
          <img src="/images/fuwa_title.webp" alt="FUWA FUWA" />
          <span className="bo-sidebar__tag">{tag}</span>
        </Link>
        <nav className="bo-nav">
          {nav.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.end} className="bo-nav__link">
              <span className="bo-nav__icon">{n.icon}</span>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="bo-sidebar__foot">FUWA FUWA e-Shop 後台</div>
      </aside>
      <div className="bo-main">
        <header className="bo-header">
          <span className="bo-header__title">{title}</span>
          <RoleSwitcher />
        </header>
        <main className="bo-content">{children}</main>
      </div>
    </div>
  </ToastProvider>
);
