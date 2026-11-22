import { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import type { Role } from '../../api/types';

/** 依角色保護路由（AAS-F-003）：未登入導向登入頁，角色不符顯示提示。 */
export const RequireRole = ({ role, children }: { role?: Role; children: ReactNode }) => {
  const { user, loading, hasRole } = useAuth();
  const location = useLocation();
  if (loading) return <div style={{ padding: 40, textAlign: 'center' }}>載入中…</div>;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (role && !hasRole(role)) {
    return (
      <div style={{ padding: 60, textAlign: 'center' }}>
        <h2>沒有權限</h2>
        <p>這個頁面需要「{role}」角色。</p>
      </div>
    );
  }
  return <>{children}</>;
};
