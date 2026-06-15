import React from 'react';
import { useUIStore } from '../../store/uiStore';
import { AlertTriangle, Info, CheckCircle } from 'lucide-react';

const GlobalDialog: React.FC = () => {
  const { dialog, closeDialog } = useUIStore();
  const [promptValue, setPromptValue] = React.useState('');

  React.useEffect(() => {
    if (dialog.isOpen && dialog.type === 'prompt') {
      setPromptValue(dialog.promptValue || '');
    }
  }, [dialog.isOpen, dialog.promptValue, dialog.type]);

  if (!dialog.isOpen) return null;

  const handleConfirm = () => {
    if (dialog.type === 'prompt') {
      dialog.onPromptConfirm?.(promptValue);
      closeDialog();
      return;
    }
    if (dialog.onConfirm) dialog.onConfirm();
    closeDialog();
  };

  const handleCancel = () => {
    if (dialog.onCancel) dialog.onCancel();
    closeDialog();
  };

  const icons = {
    alert: <Info className="text-blue-500" size={24} />,
    confirm: <CheckCircle className="text-[var(--aras-accent)]" size={24} />,
    error: <AlertTriangle className="text-rose-500" size={24} />,
    prompt: <Info className="text-[var(--aras-accent)]" size={24} />,
  };

  const colors = {
    alert: 'border-blue-100 bg-blue-50/30',
    confirm: 'border-[var(--aras-border)] bg-[color-mix(in_srgb,var(--aras-accent)_10%,transparent)]/30',
    error: 'border-rose-100 bg-rose-50/30',
    prompt: 'border-[var(--aras-border)] bg-[color-mix(in_srgb,var(--aras-accent)_10%,transparent)]/30',
  };

  const buttonColors = {
    alert: 'bg-blue-600 hover:bg-blue-700 shadow-blue-100',
    confirm: 'bg-[var(--aras-accent)] hover:brightness-110',
    error: 'bg-rose-600 hover:bg-rose-700 shadow-rose-100',
    prompt: 'bg-[var(--aras-accent)] hover:brightness-110',
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-[var(--aras-text)]/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="global-dialog-title"
        tabIndex={-1}
        className={`w-full max-w-md bg-[var(--aras-panel)] rounded-[var(--aras-radius-lg)] shadow-2xl border ${colors[dialog.type]} overflow-hidden animate-in zoom-in-95 duration-200`}
      >
        <div className="p-6">
          <div className="flex items-start gap-4">
            <div className={`p-3 rounded-[var(--aras-radius-lg)] bg-[var(--aras-panel)] border border-[var(--aras-border)] shadow-sm`}>
              {icons[dialog.type]}
            </div>
            <div className="flex-1">
              <h3 id="global-dialog-title" className="text-xl font-extrabold tracking-tight text-[var(--aras-text)]">{dialog.title}</h3>
              <p className="mt-2 text-sm text-[var(--aras-muted)] font-medium leading-relaxed whitespace-pre-wrap">
                {dialog.message}
              </p>
              {dialog.type === 'prompt' && (
                <input
                  autoFocus
                  value={promptValue}
                  onChange={(event) => setPromptValue(event.target.value)}
                  placeholder={dialog.promptPlaceholder || ''}
                  className="mt-4 w-full rounded-[var(--aras-radius)] border border-[var(--aras-border)] bg-[var(--aras-panel)] px-3 py-2 text-sm text-[var(--aras-text)] outline-none focus:border-[var(--aras-accent)]"
                />
              )}
            </div>
          </div>
        </div>

        <div className="px-6 py-4 bg-[var(--aras-panel-soft)]/50 flex items-center justify-end gap-3 border-t border-[var(--aras-border)] backdrop-blur-sm">
          {(dialog.type === 'confirm' || dialog.type === 'prompt') && (
            <button
              onClick={handleCancel}
              className="px-6 py-2.5 text-sm font-bold text-[var(--aras-muted)] hover:bg-[var(--aras-panel)] hover:shadow-sm rounded-[var(--aras-radius)] transition-all border border-transparent hover:border-[var(--aras-border)]"
            >
              {dialog.cancelLabel || 'Cancel'}
            </button>
          )}
          <button
            onClick={handleConfirm}
            className={`px-8 py-2.5 text-sm font-bold text-white rounded-[var(--aras-radius)] transition-all shadow-lg hover:shadow-xl ${buttonColors[dialog.type]}`}
          >
            {dialog.confirmLabel || 'OK'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default GlobalDialog;
