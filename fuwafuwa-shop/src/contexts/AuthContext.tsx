import { createContext, useCallback, useContext, useEffect, useState, ReactNode } from 'react';
import { get, post, tokenStore } from '../api/client';
import type { LoginResponse, Role, User } from '../api/types';

export interface RegisterData {
  loginid: string;
  name: string;
  password: string;
  email: string;
  address: string;
  phone?: string;
}

interface AuthContextType {
  user: User | null;
  /** 與舊程式相容的別名 */
  currentUser: User | null;
  loading: boolean;
  login: (loginid: string, password: string) => Promise<User>;
  register: (data: RegisterData) => Promise<User>;
  logout: () => void;
  refresh: () => Promise<void>;
  hasRole: (role: Role) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!tokenStore.get()) {
      setUser(null);
      return;
    }
    try {
      setUser(await get<User>('/auth/me'));
    } catch {
      tokenStore.set(null);
      setUser(null);
    }
  }, []);

  useEffect(() => {
    refresh().finally(() => setLoading(false));
    const onUnauthorized = () => setUser(null);
    window.addEventListener('fuwa:unauthorized', onUnauthorized);
    return () => window.removeEventListener('fuwa:unauthorized', onUnauthorized);
  }, [refresh]);

  const login = async (loginid: string, password: string) => {
    const res = await post<LoginResponse>('/auth/login', { loginid, password });
    tokenStore.set(res.access_token);
    setUser(res.user);
    return res.user;
  };

  const register = async (data: RegisterData) => {
    await post<User>('/auth/register', data);
    return login(data.loginid, data.password);
  };

  const logout = () => {
    tokenStore.set(null);
    setUser(null);
  };

  const hasRole = (role: Role) => !!user?.roles.includes(role);

  return (
    <AuthContext.Provider value={{ user, currentUser: user, loading, login, register, logout, refresh, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
};
