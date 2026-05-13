import { create } from 'zustand'
import React from 'react'

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

interface PanelState {
  isOpen: boolean;
  title: string;
  content: React.ReactNode | null;
  width: string;
}

interface UIStore {
  dialog: DialogState;
  panel: PanelState;
  showAlert: (title: string, message: string, onConfirm?: () => void) => void;
  showConfirm: (title: string, message: string, onConfirm: () => void, onCancel?: () => void) => void;
  showError: (title: string, message: string) => void;
  closeDialog: () => void;
  
  showPanel: (title: string, content: React.ReactNode, width?: string) => void;
  closePanel: () => void;
}

const defaultDialog: DialogState = {
  isOpen: false,
  title: '',
  message: '',
  type: 'alert',
}

const defaultPanel: PanelState = {
  isOpen: false,
  title: '',
  content: null,
  width: 'max-w-xl'
}

export const useUIStore = create<UIStore>((set) => ({
  dialog: defaultDialog,
  panel: defaultPanel,
  
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
  closeDialog: () => set({ dialog: defaultDialog }),

  showPanel: (title, content, width = 'max-w-xl') => set({
    panel: {
      isOpen: true,
      title,
      content,
      width
    }
  }),
  closePanel: () => set({ panel: defaultPanel })
}))
