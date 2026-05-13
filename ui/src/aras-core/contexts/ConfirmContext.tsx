import React, { createContext, useContext, useState, useCallback } from 'react'
import { GlobalDialog } from '../components/GlobalDialog'

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
        <GlobalDialog
          isOpen={true}
          onClose={handleCancel}
          title={dialog.title}
        >
          <div className="p-6">
            <p className="text-slate-600 mb-8">{dialog.message}</p>
            <div className="flex justify-end gap-3">
              <button 
                onClick={handleCancel}
                className="px-5 py-2.5 text-slate-500 font-bold hover:bg-slate-50 rounded-xl transition-colors"
              >
                {dialog.cancelText || 'Cancel'}
              </button>
              <button 
                onClick={handleConfirm}
                className={`px-5 py-2.5 rounded-xl font-bold text-white transition-all shadow-lg ${
                  dialog.type === 'danger' ? 'bg-rose-600 hover:bg-rose-700 shadow-rose-100' : 'bg-indigo-600 hover:bg-indigo-700 shadow-indigo-100'
                }`}
              >
                {dialog.confirmText || 'Confirm'}
              </button>
            </div>
          </div>
        </GlobalDialog>
      )}
    </ConfirmContext.Provider>
  )
}

export const useConfirm = () => {
  const context = useContext(ConfirmContext)
  if (!context) throw new Error('useConfirm must be used within a ConfirmProvider')
  return context.confirm
}
