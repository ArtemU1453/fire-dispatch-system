/** Notification store — transient user-facing messages (errors, info, success). */
import { create } from 'zustand';

export type NotificationSeverity = 'error' | 'warning' | 'info' | 'success';

export interface AppNotification {
  id: string;
  severity: NotificationSeverity;
  message: string;
  at: number;
  read: boolean;
}

interface NotificationState {
  items: AppNotification[];
  notify: (severity: NotificationSeverity, message: string) => void;
  markAllRead: () => void;
  dismiss: (id: string) => void;
  clear: () => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  items: [],
  notify: (severity, message) =>
    set((state) => ({
      items: [
        {
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          severity,
          message,
          at: Date.now(),
          read: false,
        },
        ...state.items,
      ].slice(0, 50),
    })),
  markAllRead: () =>
    set((state) => ({ items: state.items.map((n) => ({ ...n, read: true })) })),
  dismiss: (id) =>
    set((state) => ({ items: state.items.filter((n) => n.id !== id) })),
  clear: () => set({ items: [] }),
}));
