import { create } from 'zustand'
import { persist } from 'zustand/middleware'
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
  darkMode: boolean;
  themeMode: 'light' | 'normal' | 'dark';
  cornerMode: 'rounded' | 'square';
  density: 'compact' | 'regular' | 'comfy';
  accentColor: string;
  fontScale: number;
  pageTitle: string;
  pageSubtitle: string;
  breadcrumbs: string;
  showAlert: (title: string, message: string, onConfirm?: () => void) => void;
  showConfirm: (title: string, message: string, onConfirm: () => void, onCancel?: () => void) => void;
  showError: (title: string, message: string) => void;
  closeDialog: () => void;

  showPanel: (title: string, content: React.ReactNode, width?: string) => void;
  closePanel: () => void;
  setPageTitle: (title: string, subtitle?: string, breadcrumbs?: string) => void;
  toggleDarkMode: () => void;
  setThemeMode: (themeMode: UIStore['themeMode']) => void;
  setCornerMode: (cornerMode: UIStore['cornerMode']) => void;
  setDensity: (density: UIStore['density']) => void;
  setAccentColor: (accentColor: string) => void;
  setFontScale: (fontScale: number) => void;
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

export const useUIStore = create<UIStore>()(
  persist(
    (set, get) => ({
      dialog: defaultDialog,
      panel: defaultPanel,
      darkMode: false,
      themeMode: 'normal',
      cornerMode: 'rounded',
      density: 'regular',
      accentColor: '#7a2e2e',
      fontScale: 100,
      pageTitle: '',
      pageSubtitle: '',
      breadcrumbs: '',

      showAlert: (title, message, onConfirm) => set({
        dialog: { isOpen: true, title, message, type: 'alert', onConfirm, confirmLabel: 'OK' }
      }),
      showConfirm: (title, message, onConfirm, onCancel) => set({
        dialog: { isOpen: true, title, message, type: 'confirm', onConfirm, onCancel, confirmLabel: 'Confirm', cancelLabel: 'Cancel' }
      }),
      showError: (title, message) => set({
        dialog: { isOpen: true, title, message, type: 'error', confirmLabel: 'Close' }
      }),
      closeDialog: () => set({ dialog: defaultDialog }),

      showPanel: (title, content, width = 'max-w-xl') => set({
        panel: { isOpen: true, title, content, width }
      }),
      closePanel: () => set({ panel: defaultPanel }),

      setPageTitle: (title, subtitle = '', breadcrumbs = '') => set({
        pageTitle: title,
        pageSubtitle: subtitle,
        breadcrumbs: breadcrumbs
      }),

      toggleDarkMode: () => {
        const next = !get().darkMode
        document.documentElement.classList.toggle('dark', next)
        set({ darkMode: next, themeMode: next ? 'dark' : 'normal' })
      },
      setThemeMode: (themeMode) => {
        document.documentElement.classList.toggle('dark', themeMode === 'dark')
        set({ themeMode, darkMode: themeMode === 'dark' })
      },
      setCornerMode: (cornerMode) => set({ cornerMode }),
      setDensity: (density) => set({ density }),
      setAccentColor: (accentColor) => set({ accentColor }),
      setFontScale: (fontScale) => set({ fontScale }),
    }),
    {
      name: 'aras-ui-prefs',
      partialize: (s) => ({
        darkMode: s.darkMode,
        themeMode: s.themeMode,
        cornerMode: s.cornerMode,
        density: s.density,
        accentColor: s.accentColor,
        fontScale: s.fontScale,
      }),
      onRehydrateStorage: () => (state) => {
        if (state?.themeMode === 'dark' || state?.darkMode) document.documentElement.classList.add('dark')
      },
    }
  )
)
