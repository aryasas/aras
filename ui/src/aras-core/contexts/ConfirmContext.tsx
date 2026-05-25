import React, { createContext, useContext, useState, useCallback } from 'react'

interface ConfirmOptions {
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  type?: 'danger' | 'primary'
}

interface ConfirmContextType {
  confirm: (options: ConfirmOptions) => Promise<boolean>
}

const ConfirmContext = createContext<ConfirmContextType | undefined>(undefined)

export const ConfirmProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [dialog, setDialog] = useState<(ConfirmOptions & { resolve: (val: boolean) => void }) | null>(null)

  const confirm = useCallback((options: ConfirmOptions) => {
    return new Promise<boolean>((resolve) => {
      setDialog({ ...options, resolve })
    })
  }, [])

  const handleConfirm = () => {
    dialog?.resolve(true)
    setDialog(null)
  }

  const handleCancel = () => {
    dialog?.resolve(false)
    setDialog(null)
  }

  return (
    <ConfirmContext.Provider value={{ confirm }}>
      {children}
      {dialog && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-md bg-[var(--app-panel)] rounded-[var(--app-radius-lg)] shadow-[var(--shadow-premium)] border border-[var(--app-border)] overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="p-8">
              <h3 className="text-[calc(18px*var(--app-font-scale))] font-extrabold text-[var(--app-text)]">{dialog.title}</h3>
              <p className="text-[var(--app-muted)] text-[calc(14px*var(--app-font-scale))] mt-2 mb-8 font-semibold">{dialog.message}</p>
              <div className="flex justify-end gap-3">
                <button 
                  onClick={handleCancel}
                  className="px-6 py-2.5 text-[var(--app-muted)] font-bold hover:bg-[var(--app-panel-soft)] rounded-[var(--app-radius)] transition-colors"
                >
                  {dialog.cancelText || 'Cancel'}
                </button>
                <button 
                  onClick={handleConfirm}
                  className={`px-6 py-2.5 rounded-[var(--app-radius)] font-bold text-white transition-all shadow-lg hover:brightness-110 active:scale-95 ${
                    dialog.type === 'danger' ? 'bg-rose-500 shadow-rose-500/20' : 'bg-[var(--app-primary-action)] shadow-[var(--app-accent-glow)]'
                  }`}
                >
                  {dialog.confirmText || 'Confirm'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  )
}

export const useConfirm = () => {
  const context = useContext(ConfirmContext)
  if (!context) throw new Error('useConfirm must be used within a ConfirmProvider')
  return context.confirm
}
