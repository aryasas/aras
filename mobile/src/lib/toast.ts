import { create } from 'zustand';

export type Toast = {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
  duration?: number;
};

type ToastState = {
  toasts: Toast[];
  show: (message: string, type: Toast['type'], duration?: number) => string;
  dismiss: (id: string) => void;
};

const toastTimers = new Map<string, ReturnType<typeof setTimeout>>();

// claude-sonnet-4-6
function buildToastId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

// claude-sonnet-4-6
function clearToastTimer(id: string): void {
  const timer = toastTimers.get(id);
  if (timer) {
    clearTimeout(timer);
    toastTimers.delete(id);
  }
}

// claude-sonnet-4-6
function dismissToast(set: (fn: (state: ToastState) => ToastState) => void, id: string): void {
  clearToastTimer(id);
  set((state) => ({
    toasts: state.toasts.filter((toast) => toast.id !== id),
    show: state.show,
    dismiss: state.dismiss,
  }));
}

// claude-sonnet-4-6
function showToast(
  set: (fn: (state: ToastState) => ToastState) => void,
  message: string,
  type: Toast['type'],
  duration: number = 2500
): string {
  const id = buildToastId();
  set((state) => ({
    toasts: [...state.toasts, { id, message, type, duration }],
    show: state.show,
    dismiss: state.dismiss,
  }));

  clearToastTimer(id);
  toastTimers.set(
    id,
    setTimeout(() => {
      dismissToast(set, id);
    }, duration)
  );

  return id;
}

// claude-sonnet-4-6
export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  show: (message, type, duration) => showToast(set, message, type, duration),
  dismiss: (id) => dismissToast(set, id),
}));
