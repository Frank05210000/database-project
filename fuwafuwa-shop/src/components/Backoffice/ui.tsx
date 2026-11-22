import { CSSProperties, ReactNode, useCallback, useEffect, useRef, useState } from 'react';
import { errorMessage, ORDER_STATUS_LABEL, RETURN_STATUS_LABEL, ROLE_LABEL } from '../../api/client';

/** 把「BR-19：訊息」的規則代碼標粗顯示 */
export const RuleText = ({ text }: { text: string }) => {
  const m = text.match(/^([A-Z]{2,4}(?:-[A-Z])?(?:-\d+)?)[：:]\s*(.*)$/s);
  if (!m) return <>{text}</>;
  return (
    <>
      <span className="bo-rule">{m[1]}</span>
      {m[2]}
    </>
  );
};

export const ErrorAlert = ({ error }: { error: unknown }) => {
  if (!error) return null;
  return (
    <div className="bo-alert bo-alert--error" role="alert">
      <span>⛔</span>
      <div><RuleText text={errorMessage(error)} /></div>
    </div>
  );
};

export const Alert = ({ kind = 'info', children }: { kind?: 'info' | 'warn' | 'success' | 'error'; children: ReactNode }) => (
  <div className={`bo-alert bo-alert--${kind}`}>
    <span>{kind === 'warn' ? '⚠️' : kind === 'success' ? '✅' : kind === 'error' ? '⛔' : 'ℹ️'}</span>
    <div>{children}</div>
  </div>
);

export const PageHeader = ({ title, subtitle, actions }: { title: string; subtitle?: ReactNode; actions?: ReactNode }) => (
  <div className="bo-page-head">
    <div>
      <h1>{title}</h1>
      {subtitle && <p>{subtitle}</p>}
    </div>
    {actions && <div className="bo-page-head__actions">{actions}</div>}
  </div>
);

export const Card = ({ title, extra, children }: { title?: ReactNode; extra?: ReactNode; children: ReactNode }) => (
  <section className="bo-card">
    {(title || extra) && (
      <h2 className="bo-card__title">
        <span>{title}</span>
        {extra}
      </h2>
    )}
    {children}
  </section>
);

export const KpiCard = ({ label, value, icon, hint, accent }: { label: string; value: ReactNode; icon?: string; hint?: ReactNode; accent?: string }) => (
  <div className="bo-kpi" style={accent ? ({ '--bo-kpi-accent': accent } as CSSProperties) : undefined}>
    {icon && <span className="bo-kpi__icon">{icon}</span>}
    <div className="bo-kpi__label">{label}</div>
    <div className="bo-kpi__value">{value}</div>
    {hint && <div className="bo-kpi__hint">{hint}</div>}
  </div>
);

export const Field = ({ label, required, hint, className, children }: { label: string; required?: boolean; hint?: ReactNode; className?: string; children: ReactNode }) => (
  <label className={`bo-field ${className ?? ''}`}>
    <span className="bo-field__label">
      {label}
      {required && <span className="req">*</span>}
    </span>
    {children}
    {hint && <span className="bo-field__hint">{hint}</span>}
  </label>
);

export const Loading = () => <div className="bo-loading">載入中…</div>;
export const Empty = ({ children = '沒有資料' }: { children?: ReactNode }) => <div className="bo-empty">{children}</div>;

type BadgeTone = 'green' | 'amber' | 'blue' | 'rose' | 'red' | 'primary' | 'gray';
export const Badge = ({ tone = 'gray', children }: { tone?: BadgeTone; children: ReactNode }) => (
  <span className={`bo-badge bo-badge--${tone}`}>{children}</span>
);

const ORDER_TONE: Record<string, BadgeTone> = {
  received: 'blue', processing: 'amber', shipping: 'primary', closed: 'green', cancelled: 'gray', returned: 'rose',
};
const RETURN_TONE: Record<string, BadgeTone> = { pending: 'amber', approved: 'green', rejected: 'red' };
const ROLE_TONE: Record<string, BadgeTone> = { customer: 'blue', staff: 'amber', admin: 'primary' };

export const OrderStatusBadge = ({ status }: { status: string }) => (
  <Badge tone={ORDER_TONE[status]}>{ORDER_STATUS_LABEL[status] ?? status}</Badge>
);
export const ReturnStatusBadge = ({ status }: { status: string }) => (
  <Badge tone={RETURN_TONE[status]}>{RETURN_STATUS_LABEL[status] ?? status}</Badge>
);
export const RoleChip = ({ role }: { role: string }) => <Badge tone={ROLE_TONE[role]}>{ROLE_LABEL[role] ?? role}</Badge>;

export const Tabs = <T extends string>({ value, options, onChange }: { value: T; options: { value: T; label: string }[]; onChange: (v: T) => void }) => (
  <div className="bo-tabs" role="tablist">
    {options.map((o) => (
      <button key={o.value} type="button" role="tab" aria-selected={o.value === value} className={`bo-tab ${o.value === value ? 'active' : ''}`} onClick={() => onChange(o.value)}>
        {o.label}
      </button>
    ))}
  </div>
);

/** 簡單的長條圖（純 CSS） */
export const BarList = ({ rows, format }: { rows: { label: string; value: number }[]; format: (n: number) => string }) => {
  const max = Math.max(1, ...rows.map((r) => r.value));
  if (rows.length === 0) return <Empty />;
  return (
    <div className="bo-bars">
      {rows.map((r) => (
        <div className="bo-bar" key={r.label}>
          <span className="bo-bar__label" title={r.label}>{r.label}</span>
          <div className="bo-bar__track"><div className="bo-bar__fill" style={{ width: `${(r.value / max) * 100}%` }} /></div>
          <span className="bo-bar__value">{format(r.value)}</span>
        </div>
      ))}
    </div>
  );
};

/** 載入資料：回傳 data / loading / error / reload */
export function useLoad<T>(loader: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const seq = useRef(0);
  const loaderRef = useRef(loader);
  loaderRef.current = loader;

  const reload = useCallback(async () => {
    const my = ++seq.current;
    setLoading(true);
    setError(null);
    try {
      const d = await loaderRef.current();
      if (my === seq.current) setData(d);
    } catch (e) {
      if (my === seq.current) setError(e);
    } finally {
      if (my === seq.current) setLoading(false);
    }
  }, []);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { reload(); }, deps);

  return { data, setData, loading, error, reload };
}

/** 日期工具（以本地時區產生 YYYY-MM-DD） */
export const isoDate = (d: Date = new Date()): string => {
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
};
export const addDays = (days: number, base: Date = new Date()): string => {
  const d = new Date(base);
  d.setDate(d.getDate() + days);
  return isoDate(d);
};
export const formatDate = (s: string | null | undefined): string => (s ? s.slice(0, 10) : '—');
