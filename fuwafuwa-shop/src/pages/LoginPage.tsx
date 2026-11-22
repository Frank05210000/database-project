import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useLanguage } from '../i18n';
import { useAuth } from '../contexts/AuthContext';
import { errorMessage } from '../api/client';
import type { User } from '../api/types';
import './LoginPage.css';

const DEMO_ACCOUNTS = [
  { loginid: 'alice', password: 'customer123', role: '顧客 / customer' },
  { loginid: 'staff', password: 'staff123', role: '工作人員 / staff' },
  { loginid: 'admin', password: 'admin123', role: '平台管理員 / admin' },
];

const emptyRegister = { loginid: '', name: '', password: '', email: '', address: '', phone: '' };

export const LoginPage: React.FC = () => {
  const { t } = useLanguage();
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from;

  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [loginid, setLoginid] = useState('');
  const [password, setPassword] = useState('');
  const [form, setForm] = useState(emptyRegister);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  /** 依角色導向：只有工作人員角色 → /staff；只有平台管理 → /admin；顧客回到原本的頁面 */
  const redirectAfterLogin = (user: User) => {
    const roles = user.roles;
    if (!roles.includes('customer')) {
      if (roles.includes('staff')) return navigate('/staff', { replace: true });
      if (roles.includes('admin')) return navigate('/admin', { replace: true });
    }
    const target = from && from !== '/login' && !from.startsWith('/staff') && !from.startsWith('/admin') ? from : '/';
    navigate(target, { replace: true });
  };

  const run = async (fn: () => Promise<User>) => {
    try {
      setError('');
      setLoading(true);
      redirectAfterLogin(await fn());
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    run(() => login(loginid.trim(), password));
  };

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    run(() =>
      register({
        loginid: form.loginid.trim(),
        name: form.name.trim(),
        password: form.password,
        email: form.email.trim(),
        address: form.address.trim(),
        phone: form.phone.trim() || undefined,
      }),
    );
  };

  const field = (key: keyof typeof emptyRegister, label: string, type = 'text', required = true) => (
    <div className="form-group">
      <label htmlFor={`reg-${key}`} className="form-label">
        {label}
      </label>
      <input
        id={`reg-${key}`}
        type={type}
        className="form-input"
        value={form[key]}
        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
        required={required}
        disabled={loading}
      />
    </div>
  );

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <div className="login-logo">🐾</div>
            <h1 className="login-title">{mode === 'login' ? t.login.title : t.login.registerTitle}</h1>
            <p className="login-subtitle">{mode === 'login' ? t.login.subtitle : t.login.registerSubtitle}</p>
          </div>

          {mode === 'login' ? (
            <form className="login-form" onSubmit={handleLogin}>
              {error && <div className="error-message">{error}</div>}
              <div className="form-group">
                <label htmlFor="loginid" className="form-label">
                  {t.login.loginid}
                </label>
                <input
                  id="loginid"
                  className="form-input"
                  placeholder={t.login.loginidPlaceholder}
                  value={loginid}
                  onChange={(e) => setLoginid(e.target.value)}
                  autoComplete="username"
                  required
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label htmlFor="password" className="form-label">
                  {t.login.password}
                </label>
                <input
                  type="password"
                  id="password"
                  className="form-input"
                  placeholder={t.login.passwordPlaceholder}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                  disabled={loading}
                />
              </div>
              <button type="submit" className="login-button" disabled={loading}>
                {loading ? t.login.loggingIn : t.login.loginButton}
              </button>
            </form>
          ) : (
            <form className="login-form" onSubmit={handleRegister}>
              {error && <div className="error-message">{error}</div>}
              {field('loginid', t.login.loginid)}
              {field('name', t.login.name)}
              {field('password', t.login.password, 'password')}
              {field('email', t.login.email, 'email')}
              {field('address', t.login.address)}
              {field('phone', t.login.phone, 'tel', false)}
              <button type="submit" className="login-button" disabled={loading}>
                {loading ? t.login.registering : t.login.registerButton}
              </button>
            </form>
          )}

          <div className="signup-link">
            {mode === 'login' ? t.login.noAccount : t.login.haveAccount}{' '}
            <a
              href="#"
              className="signup-link-button"
              onClick={(e) => {
                e.preventDefault();
                setError('');
                setMode(mode === 'login' ? 'register' : 'login');
              }}
            >
              {mode === 'login' ? t.login.signUp : t.login.signIn}
            </a>
          </div>

          {mode === 'login' && (
            <div className="login-demo">
              <div className="login-demo__title">{t.login.demoAccounts}</div>
              {DEMO_ACCOUNTS.map((a) => (
                <button
                  key={a.loginid}
                  type="button"
                  className="login-demo__item"
                  onClick={() => {
                    setLoginid(a.loginid);
                    setPassword(a.password);
                  }}
                >
                  <code>
                    {a.loginid} / {a.password}
                  </code>
                  <span>{a.role}</span>
                </button>
              ))}
            </div>
          )}

          <button onClick={() => navigate('/')} className="back-button">
            {t.login.backToHome}
          </button>
        </div>
      </div>
    </div>
  );
};
