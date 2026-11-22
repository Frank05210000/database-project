import { createContext, ReactNode, useCallback, useContext, useMemo, useRef, useState } from 'react';
import { errorMessage } from '../../api/client';
import { RuleText } from './ui';

type ToastKind = 'error' | 'success' | 'info';
interface ToastItem { id: number; kind: ToastKind; title?: string; message: string }

interface ToastApi {
  success: (message: string, title?: string) => void;
  info: (message: string, title?: string) => void;
  /** 顯示後端錯誤（ApiError.message，例如「BR-19：…」） */
  error: (e: unknown, title?: string) => void;
}

const ToastContext = createContext<ToastApi | null>(null);

export const useToast = (): ToastApi => {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
};

const DEFAULT_TITLE: Record<ToastKind, string> = { error: '操作被拒絕', success: '完成', info: '提示' };

export const ToastProvider = ({ children }: { children: ReactNode }) => {
  const [items, setItems] = useState<ToastItem[]>([]);
  const nextId = useRef(1);

  const remove = useCallback((id: number) => setItems((xs) => xs.filter((x) => x.id !== id)), []);

  const push = useCallback(
    (kind: ToastKind, message: string, title?: string) => {
      const id = nextId.current++;
      setItems((xs) => [...xs.slice(-4), { id, kind, message, title }]);
      // 錯誤訊息停留較久，方便展示商業規則
      window.setTimeout(() => remove(id), kind === 'error' ? 9000 : 4000);
    },
    [remove],
  );

  const api = useMemo<ToastApi>(
    () => ({
      success: (m, t) => push('success', m, t),
      info: (m, t) => push('info', m, t),
      error: (e, t) => push('error', typeof e === 'string' ? e : errorMessage(e), t),
    }),
    [push],
  );

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="bo-toasts" role="status" aria-live="polite">
        {items.map((t) => (
          <div key={t.id} className={`bo-toast bo-toast--${t.kind}`}>
            <span>{t.kind === 'error' ? '⛔' : t.kind === 'success' ? '✅' : 'ℹ️'}</span>
            <div className="bo-toast__body">
              <div className="bo-toast__title">{t.title ?? DEFAULT_TITLE[t.kind]}</div>
              <RuleText text={t.message} />
            </div>
            <button className="bo-toast__close" onClick={() => remove(t.id)} aria-label="關閉">×</button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};
