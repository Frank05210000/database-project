import { FormEvent, ReactNode, useEffect } from 'react';

interface ModalProps {
  title: ReactNode;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  wide?: boolean;
  /** 傳入時整個 modal 包在 <form> 中，按 Enter 會送出 */
  onSubmit?: () => void;
}

export const Modal = ({ title, onClose, children, footer, wide, onSubmit }: ModalProps) => {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const inner = (
    <>
      <div className="bo-modal__head">
        <h2>{title}</h2>
        <button type="button" className="bo-btn bo-btn--ghost bo-btn--sm" onClick={onClose} aria-label="關閉">✕</button>
      </div>
      <div className="bo-modal__body">{children}</div>
      {footer && <div className="bo-modal__foot">{footer}</div>}
    </>
  );

  return (
    <div className="bo-modal-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className={`bo-modal ${wide ? 'bo-modal--wide' : ''}`} role="dialog" aria-modal="true">
        {onSubmit ? (
          <form onSubmit={(e: FormEvent) => { e.preventDefault(); onSubmit(); }}>{inner}</form>
        ) : inner}
      </div>
    </div>
  );
};

/** 確認對話框 */
export const ConfirmModal = ({ title, message, confirmLabel = '確定', danger, busy, onConfirm, onClose }: {
  title: string; message: ReactNode; confirmLabel?: string; danger?: boolean; busy?: boolean;
  onConfirm: () => void; onClose: () => void;
}) => (
  <Modal
    title={title}
    onClose={onClose}
    footer={
      <>
        <button type="button" className="bo-btn bo-btn--ghost" onClick={onClose}>取消</button>
        <button type="button" className={`bo-btn ${danger ? 'bo-btn--danger' : ''}`} disabled={busy} onClick={onConfirm}>{confirmLabel}</button>
      </>
    }
  >
    {message}
  </Modal>
);
