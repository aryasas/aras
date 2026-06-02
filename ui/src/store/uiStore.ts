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

export interface CustomElementDef {
  id: string;
  type: 'text' | 'button' | 'divider' | 'container' | 'html';
  parentId: string;
  content?: string;
  props?: Record<string, any>;
}

interface UIStore {
  dialog: DialogState;
  panel: PanelState;
  darkMode: boolean;
  themeMode: 'light' | 'dark';
  cornerMode: 'rounded' | 'square';
  density: 'compact' | 'regular' | 'comfy';
  accentColor: string;
  fontScale: number;
  dirtyForms: Set<string>;
  sidebarCollapsed: boolean;
  iconRailCollapsed: boolean;
  topbarNavStyle: 'icon-text' | 'icon-only';
  inlineEdit: boolean;
  designMode: boolean;
  activeElementId: string | null;
  designData: {
    styles: Record<string, any>;
    orders: Record<string, string[]>;
    customElements: Record<string, CustomElementDef>;
  };
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
  toggleSidebar: () => void;
  toggleIconRail: () => void;
  setTopbarNavStyle: (style: UIStore['topbarNavStyle']) => void;
  setThemeMode: (themeMode: UIStore['themeMode']) => void;
  setCornerMode: (cornerMode: UIStore['cornerMode']) => void;
  setDensity: (density: UIStore['density']) => void;
  setAccentColor: (accentColor: string) => void;
  setFontScale: (fontScale: number) => void;
  setDirty: (key: string, dirty: boolean) => void;
  setInlineEdit: (v: boolean) => void;
  toggleDesignMode: () => void;
  setActiveDesignElement: (id: string | null) => void;
  updateElementStyle: (id: string, styles: any) => void;
  updateElementOrder: (containerId: string, order: string[]) => void;
  addCustomElement: (element: CustomElementDef) => void;
  updateCustomElement: (id: string, updates: Partial<CustomElementDef>) => void;
  removeCustomElement: (id: string) => void;
  setDesignData: (data: { styles: Record<string, any>; orders: Record<string, string[]>; customElements?: Record<string, CustomElementDef> }) => void;
  submenuOrder: Record<string, string[]>;
  setSubmenuOrder: (appName: string, order: string[]) => void;
  mobileSidebarOpen: boolean;
  setMobileSidebarOpen: (open: boolean) => void;
  fullWidth: boolean;
  setFullWidth: (v: boolean) => void;
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
      themeMode: 'light',
      cornerMode: 'rounded',
      density: 'regular',
      accentColor: '#4F46E5',
      fontScale: 100,
      dirtyForms: new Set<string>(),
      sidebarCollapsed: false,
      iconRailCollapsed: false,
      topbarNavStyle: 'icon-text',
      inlineEdit: false,
      designMode: false,
      activeElementId: null,
      designData: { styles: {}, orders: {}, customElements: {} },
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
        set({ darkMode: next, themeMode: next ? 'dark' : 'light' })
      },
      toggleSidebar: () => set({ sidebarCollapsed: !get().sidebarCollapsed }),
      toggleIconRail: () => set({ iconRailCollapsed: !get().iconRailCollapsed }),
      setTopbarNavStyle: (topbarNavStyle) => set({ topbarNavStyle }),
      setThemeMode: (themeMode) => {
        document.documentElement.classList.toggle('dark', themeMode === 'dark')
        document.documentElement.setAttribute('data-theme', themeMode === 'dark' ? 'dark' : 'light')
        set({ themeMode, darkMode: themeMode === 'dark' })
      },
      setCornerMode: (cornerMode) => set({ cornerMode }),
      setDensity: (density) => set({ density }),
      setAccentColor: (accentColor) => set({ accentColor }),
      setFontScale: (fontScale) => set({ fontScale }),
      setDirty: (key, dirty) => set((state) => {
        const next = new Set(state.dirtyForms)
        if (dirty) next.add(key)
        else next.delete(key)
        return { dirtyForms: next }
      }),
      setInlineEdit: (inlineEdit) => set({ inlineEdit }),
      toggleDesignMode: () => set({ designMode: !get().designMode, activeElementId: null }),
      setActiveDesignElement: (id) => set({ activeElementId: id }),
      updateElementStyle: (id, styles) => set((state) => ({
        designData: {
          ...state.designData,
          styles: { ...state.designData.styles, [id]: { ...state.designData.styles[id], ...styles } }
        }
      })),
      updateElementOrder: (containerId, order) => set((state) => ({
        designData: {
          ...state.designData,
          orders: { ...state.designData.orders, [containerId]: order }
        }
      })),
      addCustomElement: (element) => set((state) => {
        const parentOrder = state.designData.orders[element.parentId] || [];
        return {
          designData: {
            ...state.designData,
            customElements: { ...state.designData.customElements, [element.id]: element },
            orders: { ...state.designData.orders, [element.parentId]: [...parentOrder, element.id] }
          }
        };
      }),
      updateCustomElement: (id, updates) => set((state) => {
        const el = state.designData.customElements[id];
        if (!el) return state;
        return {
          designData: {
            ...state.designData,
            customElements: { ...state.designData.customElements, [id]: { ...el, ...updates } }
          }
        };
      }),
      removeCustomElement: (id) => set((state) => {
        const newElements = { ...state.designData.customElements };
        const el = newElements[id];
        if (!el) return state;
        delete newElements[id];
        const newOrders = { ...state.designData.orders };
        if (newOrders[el.parentId]) {
          newOrders[el.parentId] = newOrders[el.parentId].filter(eid => eid !== id);
        }
        return {
          designData: { ...state.designData, customElements: newElements, orders: newOrders }
        };
      }),
      setDesignData: (data) => set({ designData: { styles: data.styles || {}, orders: data.orders || {}, customElements: data.customElements || {} } }),
      submenuOrder: {},
      setSubmenuOrder: (appName, order) => set((s) => ({ submenuOrder: { ...s.submenuOrder, [appName]: order } })),
      mobileSidebarOpen: false,
      setMobileSidebarOpen: (open) => set({ mobileSidebarOpen: open }),
      fullWidth: false,
      setFullWidth: (fullWidth) => set({ fullWidth }),
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
        sidebarCollapsed: s.sidebarCollapsed,
        iconRailCollapsed: s.iconRailCollapsed,
        topbarNavStyle: s.topbarNavStyle,
        inlineEdit: s.inlineEdit,
        submenuOrder: s.submenuOrder,
      }),
      migrate: (persisted: any) => {
        if (persisted?.themeMode && persisted.themeMode !== 'dark') persisted.themeMode = 'light'
        return persisted
      },
      onRehydrateStorage: () => (state) => {
        const mode = state?.themeMode === 'dark' ? 'dark' : 'light'
        if (mode === 'dark' || state?.darkMode) document.documentElement.classList.add('dark')
        document.documentElement.setAttribute('data-theme', mode)
      },
    }
  )
)
