import { createContext, useCallback, useContext, useState } from 'react';

const ToastCtx = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const push = useCallback((t) => {
    const id = Math.random().toString(36).slice(2, 9);
    const toast = { id, kind: 'info', ttl: 4000, ...t };
    setToasts((cur) => [...cur, toast]);
    setTimeout(() => setToasts((cur) => cur.filter((x) => x.id !== id)), toast.ttl);
  }, []);

  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="toast-container">
        {toasts.map((t) => (
          <div key={t.id} className={`toast ${t.kind}`}>
            {t.title && <div className="title">{t.title}</div>}
            <div className="msg">{t.message}</div>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

export function useToast() {
  return useContext(ToastCtx);
}
