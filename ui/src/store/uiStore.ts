import { create } from 'zustand'

interface DialogState {
  isOpen: boolean;
  title: string;
  message: string;
  type: 'alert' | 'confirm' | 'error';
  onConfirm?: () => void;
  onCancel?: () => void;
  confirmLabel?: string;
  cancelLabel?: string;
}

interface UIStore {
  dialog: DialogState;
  showAlert: (title: string, message: string, onConfirm?: () => void) => void;
  showConfirm: (title: string, message: string, onConfirm: () => void, onCancel?: () => void) => void;
  showError: (title: string, message: string) => void;
  closeDialog: () => void;
}

const defaultDialog: DialogState = {
  isOpen: false,
  title: '',
  message: '',
  type: 'alert',
}

export const useUIStore = create<UIStore>((set) => ({
  dialog: defaultDialog,
  showAlert: (title, message, onConfirm) => set({
    dialog: {
      isOpen: true,
      title,
      message,
      type: 'alert',
      onConfirm,
      confirmLabel: 'OK'
    }
  }),
  showConfirm: (title, message, onConfirm, onCancel) => set({
    dialog: {
      isOpen: true,
      title,
      message,
      type: 'confirm',
      onConfirm,
      onCancel,
      confirmLabel: 'Confirm',
      cancelLabel: 'Cancel'
    }
  }),
  showError: (title, message) => set({
    dialog: {
      isOpen: true,
      title,
      message,
      type: 'error',
      confirmLabel: 'Close'
    }
  }),
  closeDialog: () => set({ dialog: defaultDialog })
}))
