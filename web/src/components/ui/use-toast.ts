import { create } from "zustand";

export type ToastVariant = "default" | "success" | "warning" | "danger" | "info";

export interface ToastItem {
  id: string;
  title?: string;
  description?: string;
  variant: ToastVariant;
}

interface ToastState {
  toasts: ToastItem[];
  toast: (t: Omit<ToastItem, "id" | "variant"> & { variant?: ToastVariant }) => string;
  dismiss: (id: string) => void;
}

export const useToast = create<ToastState>((set) => ({
  toasts: [],
  toast: ({ variant = "default", ...rest }) => {
    const id = crypto.randomUUID();
    set((s) => ({ toasts: [...s.toasts, { id, variant, ...rest }] }));
    setTimeout(() => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })), 5000);
    return id;
  },
  dismiss: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));
