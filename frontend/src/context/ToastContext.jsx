import React, { createContext, useState, useCallback, useContext } from 'react';
import { CheckCircle, AlertCircle, Info, X } from 'lucide-react';

const ToastCtx = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  
  const add = useCallback((msg, type = 'info', dur = 3500) => {
    const id = Date.now() + Math.random();
    setToasts(t => [...t, { id, msg, type }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), dur);
  }, []);

  const icn = { success: <CheckCircle size={14} />, error: <AlertCircle size={14} />, info: <Info size={14} /> };
  const col = { success: 'var(--green)', error: 'var(--red)', info: 'var(--blue)' };

  return (
    <ToastCtx.Provider value={add}>
      {children}
      <div className="toast-container">
        {toasts.map(t => (
          <div key={t.id} className="toast animate-slide-in" style={{ borderLeft: `3px solid ${col[t.type]}` }}>
            <div style={{ color: col[t.type], display: 'flex', alignItems: 'center' }}>{icn[t.type]}</div>
            <div style={{ flex: 1, fontSize: 13, fontWeight: 500 }}>{t.msg}</div>
            <button onClick={() => setToasts(ts => ts.filter(x => x.id !== t.id))} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

export function useToast() {
  return useContext(ToastCtx);
}
