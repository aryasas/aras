import React from 'react';
import { useUIStore } from '../../store/uiStore';
import { AlertTriangle, Info, CheckCircle } from 'lucide-react';

const GlobalDialog: React.FC = () => {
  const { dialog, closeDialog } = useUIStore();

  if (!dialog.isOpen) return null;

  const handleConfirm = () => {
    if (dialog.onConfirm) dialog.onConfirm();
    closeDialog();
  };

  const handleCancel = () => {
    if (dialog.onCancel) dialog.onCancel();
    closeDialog();
  };

  const icons = {
    alert: <Info className="text-blue-500" size={24} />,
    confirm: <CheckCircle className="text-indigo-500" size={24} />,
    error: <AlertTriangle className="text-rose-500" size={24} />,
  };

  const colors = {
    alert: 'border-blue-100 bg-blue-50/30',
    confirm: 'border-indigo-100 bg-indigo-50/30',
    error: 'border-rose-100 bg-rose-50/30',
  };

  const buttonColors = {
    alert: 'bg-blue-600 hover:bg-blue-700 shadow-blue-100',
    confirm: 'bg-indigo-600 hover:bg-indigo-700 shadow-indigo-100',
    error: 'bg-rose-600 hover:bg-rose-700 shadow-rose-100',
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="global-dialog-title"
        tabIndex={-1}
        className={`w-full max-w-md bg-white rounded-3xl shadow-2xl border ${colors[dialog.type]} overflow-hidden animate-in zoom-in-95 duration-200`}
      >
        <div className="p-6">
          <div className="flex items-start gap-4">
            <div className={`p-3 rounded-2xl bg-white border border-slate-100 shadow-sm`}>
              {icons[dialog.type]}
            </div>
            <div className="flex-1">
              <h3 id="global-dialog-title" className="text-xl font-extrabold tracking-tight text-slate-900">{dialog.title}</h3>
              <p className="mt-2 text-sm text-slate-500 font-medium leading-relaxed whitespace-pre-wrap">
                {dialog.message}
              </p>
            </div>
          </div>
        </div>

        <div className="px-6 py-4 bg-slate-50/50 flex items-center justify-end gap-3 border-t border-slate-100 backdrop-blur-sm">
          {dialog.type === 'confirm' && (
            <button
              onClick={handleCancel}
              className="px-6 py-2.5 text-sm font-bold text-slate-600 hover:bg-white hover:shadow-sm rounded-xl transition-all border border-transparent hover:border-slate-200"
            >
              {dialog.cancelLabel || 'Cancel'}
            </button>
          )}
          <button
            onClick={handleConfirm}
            className={`px-8 py-2.5 text-sm font-bold text-white rounded-xl transition-all shadow-lg hover:shadow-xl ${buttonColors[dialog.type]}`}
          >
            {dialog.confirmLabel || 'OK'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default GlobalDialog;
